import re

from Xlib import X, Xatom
import Xlib.display
from Xlib.XK import string_to_keysym, load_keysym_group
from Xlib.protocol.event import ClientMessage

MODIFICATORS = {
  'Alt': X.Mod1Mask,
  'Control': X.ControlMask,
  'Ctrl': X.ControlMask,
  'Shift': X.ShiftMask,
  'Win': X.Mod4Mask,
  'Mod': X.Mod4Mask,
}

IGNORED_MOD_MASKS = (0, X.LockMask, X.Mod2Mask)

load_keysym_group('xf86')

class WM(object):
    def __init__(self):
        self.key_handlers = {}
        self.property_handlers = {}
        self.create_handlers = []
        self.destroy_handlers = {}

        self.re_cache = {}

        self.dpy = Xlib.display.Display()
        self.root = self.dpy.screen().root
        self.root.change_attributes(
            event_mask=X.KeyPressMask | X.SubstructureNotifyMask )

    def bind_key(self, window, key):
        parts = key.split('+')
        mod, key = parts[:-1], parts[-1]
        modmask = 0
        for m in mod:
            try:
                modmask |= MODIFICATORS[m]
            except KeyError:
                raise Exception('Invalid modificator [%s]' % m)

        sym = string_to_keysym(key)
        if sym is X.NoSymbol:
            raise Exception('Invalid key name [%s]' % key)

        code = self.dpy.keysym_to_keycode(sym)

        def inner(func):
            for imask in IGNORED_MOD_MASKS:
                mask = modmask | imask
                window.grab_key(code, mask, True, X.GrabModeAsync, X.GrabModeAsync)
                self.key_handlers.setdefault(window.id, {})[(mask, code)] = func

            return func

        return inner

    def on_key(self, key):
        return self.bind_key(self.root, key)

    def on_create(self, *args, **matchers):
        if args:
            self.create_handlers.append(args[0])
            return args[0]

        def inner(func):
            def match_window(wm):
                if wm.is_match(wm.event_window, **matchers):
                    func(wm)

            self.create_handlers.append(match_window)
            return func

        return inner

    def on_destroy(self, window):
        def inner(func):
            self.destroy_handlers.setdefault(window.id, []).append(func)
            return func

        return inner

    def on_property_change(self, *props):
        def inner(func):
            for p in props:
                atom = self.dpy.intern_atom(p)
                self.property_handlers.setdefault(atom, []).append(func)

            return func

        return inner

    def get_clients(self):
        result = []
        wids = self.root.get_full_property(self.get_atom('_NET_CLIENT_LIST'), Xatom.WINDOW).value

        for wid in wids:
            result.append(self.dpy.create_resource_object('window', wid))

        return result

    @property
    def current_window(self):
        result = self.root.get_full_property(self.get_atom('_NET_ACTIVE_WINDOW'), Xatom.WINDOW)
        if result:
            return self.dpy.create_resource_object('window', result.value[0])

        return None

    @property
    def current_desktop(self):
        return self.root.get_full_property(
            self.dpy.intern_atom('_NET_CURRENT_DESKTOP'), 0).value[0]

    def get_window_desktop(self, window):
        d = window.get_full_property(self.dpy.intern_atom('_NET_WM_DESKTOP'), 0)
        if d:
            d = d.value[0]
            if d == 0xffffffff:
                return -1
            else:
                return d
        else:
            return None

    def set_current_desktop(self, num):
        if num < 0:
            return

        self._send_event(self.root, self.dpy.intern_atom('_NET_CURRENT_DESKTOP'), [num])
        self.dpy.flush()

    def _send_event(self, window, ctype, data, mask=None):
        data = (data + ([0] * (5 - len(data))))[:5]
        ev = ClientMessage(window=window, client_type=ctype, data=(32, (data)))
        self.root.send_event(ev, event_mask=X.SubstructureRedirectMask)

    def get_window_role(self, window):
        d = window.get_full_property(
            self.dpy.intern_atom('WM_WINDOW_ROLE'), Xatom.STRING)
        if d is None or d.format != 8:
            return None
        else:
            return d.value

    def match_string(self, pattern, data):
        if not data:
            return False

        try:
            r = self.re_cache[pattern]
        except KeyError:
            r = self.re_cache[pattern] = re.compile(pattern)

        return r.match(data)

    def is_match(self, window, name=None, cls=None, role=None, desktop=None):
        match = True
        try:
            wname, wclass = window.get_wm_class()
        except TypeError:
            wname = wclass = None

        if match and name:
            match = self.match_string(name, wname)

        if match and cls:
            match = self.match_string(cls, wclass)

        if match and role:
            match = self.match_string(role, self.get_window_role(window))

        if match and desktop:
            match = self.get_window_desktop(window) == desktop

        return match

    def find_client(self, clients, **matchers):
        result = []
        for c in clients:
            if self.is_match(c, **matchers):
                result.append(c)

        return result

    def handle_create(self, window):
        window.change_attributes(
            event_mask=X.KeyPressMask | X.StructureNotifyMask | X.PropertyChangeMask )

        self.event_window = window
        for handler in self.create_handlers:
            handler(self)

    def run(self):
        self.startup = True
        for c in self.get_clients():
            self.handle_create(c)

        while True:
            try:
                event = self.dpy.next_event()
                etype = event.type
                if etype == X.KeyPress:
                    try:
                        handler = self.key_handlers[event.window.id][(event.state, event.detail)]
                    except KeyError:
                        pass
                    else:
                        self.event = event
                        self.event_window = event.window
                        handler(self)

                elif etype == X.KeyRelease:
                    pass

                elif etype == X.CreateNotify:
                    self.event = event
                    self.startup = False
                    self.handle_create(event.window)

                elif etype == X.DestroyNotify:
                    wid = event.window.id
                    if wid in self.key_handlers:
                        del self.key_handlers[wid]

                    try:
                        handlers = self.destroy_handlers[event.window.id]
                    except KeyError:
                        pass
                    else:
                        self.event = event
                        self.event_window = event.window
                        for h in handlers:
                            h(self)

                        del self.destroy_handlers[event.window.id]

                elif etype == X.PropertyNotify:
                    atom = event.atom
                    if atom in self.property_handlers:
                        self.event_window = event.window
                        self.event = event
                        for h in self.property_handlers[atom]:
                            h(self)
            except (KeyboardInterrupt, SystemExit):
                break
            except:
                import logging
                logging.getLogger(__name__).exception('Boo')

    def focus_and_raise(self, window):
        self.activate_window_desktop(window)
        window.configure(stack_mode=X.Above)
        window.set_input_focus(X.RevertToPointerRoot, X.CurrentTime)
        self.dpy.flush()

    def place_window_above(self, window):
        window.configure(stack_mode=X.Above)
        self.dpy.flush()

    def place_window_below(self, window):
        window.configure(stack_mode=X.Below)
        self.dpy.flush()

    def activate_window_desktop(self, window):
        wd = self.get_window_desktop(window)
        if wd is not None:
            if self.current_desktop != wd:
                self.set_current_desktop(wd)
                return True
            else:
                return False
        else:
            return None

    def get_atom(self, atom_name):
        return self.dpy.get_atom(atom_name)

    def get_atom_name(self, atom):
        return self.dpy.get_atom_name(atom)