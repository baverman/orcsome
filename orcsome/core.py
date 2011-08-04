from Xlib import X, Xatom
import Xlib.display
from Xlib.XK import string_to_keysym
from Xlib.protocol.event import ClientMessage

mods = {
  'Alt': X.Mod1Mask,
  'Control': X.ControlMask,
  'Ctrl': X.ControlMask,
  'Shift': X.ShiftMask,
  'Win': X.Mod4Mask,
  'Mod': X.Mod4Mask,
}

class WM(object):
    def __init__(self):
        self.key_handlers = {}
        self.create_handlers = []

        self.dpy = Xlib.display.Display()
        self.root = self.dpy.screen().root
        self.root.change_attributes(
            event_mask=X.KeyPressMask | X.SubstructureNotifyMask )

    def bind_key(self, window, key):
        parts = key.split('+')
        mod, key = parts[:-1], parts[-1]
        modmask = 0
        for m in mod:
            modmask |= mods[m]

        code = self.dpy.keysym_to_keycode(string_to_keysym(key))
        window.grab_key(code, modmask, True, X.GrabModeAsync, X.GrabModeAsync)

        def inner(func):
            self.key_handlers.setdefault(window.id, {})[(modmask, code)] = func
            return func

        return inner

    def on_key(self, key):
        return self.bind_key(self.root, key)

    def on_create(self, func):
        self.create_handlers.append(func)
        return func

    def get_clients(self):
        result = []
        wids = self.root.get_full_property(
            self.dpy.intern_atom('_NET_CLIENT_LIST'), Xatom.WINDOW).value

        for wid in wids:
            result.append(self.dpy.create_resource_object('window', wid))

        return result

    @property
    def current_desktop(self):
        return self.root.get_full_property(
            self.dpy.intern_atom('_NET_CURRENT_DESKTOP'), 0).value[0]

    def get_window_desktop(self, window):
        return window.get_full_property(
            self.dpy.intern_atom('_NET_WM_DESKTOP'), 0).value[0]

    def set_current_desktop(self, num):
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

    def is_match(self, window, name=None, cls=None, role=None, desktop=None):
        match = True
        try:
            wname, wclass = window.get_wm_class()
        except TypeError:
            wname = wclass = None

        if match and name:
            match = name == wname

        if match and cls:
            match = cls == wclass

        if match and role:
            match = self.get_window_role(window) == role

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
            event_mask=X.KeyPressMask | X.StructureNotifyMask )

        for handler in self.create_handlers:
            self.event_window = window
            handler(self)

    def run(self):
        for c in self.get_clients():
            self.handle_create(c)

        while True:
            event = self.dpy.next_event()
            if event.type == X.KeyPress:
                try:
                    handler = self.key_handlers[event.window.id][(event.state, event.detail)]
                except KeyError:
                    pass
                else:
                    self.event_window = event.window
                    handler(self)
            elif event.type == X.KeyRelease:
                pass
            elif event.type == X.CreateNotify:
                self.handle_create(event.window)
            elif event.type == X.DestroyNotify:
                wid = event.window.id
                if wid in self.key_handlers:
                    del self.key_handlers[wid]
            else:
                pass
                #print event

    def focus_and_raise(self, window):
        wdesktop = self.get_window_desktop(window)
        if wdesktop != self.current_desktop:
            self.set_current_desktop(wdesktop)

        window.configure(stack_mode=X.Above)
        window.set_input_focus(X.RevertToPointerRoot, X.CurrentTime)
        self.dpy.flush()
