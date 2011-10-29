import re
import os, fcntl
from collections import namedtuple
import logging
from select import select

from Xlib import X, Xatom
from Xlib.error import BadWindow
import Xlib.display
from Xlib.XK import string_to_keysym, load_keysym_group
from Xlib.protocol.event import ClientMessage

from .xext import screen_saver

MODIFICATORS = {
  'Alt': X.Mod1Mask,
  'Control': X.ControlMask,
  'Ctrl': X.ControlMask,
  'Shift': X.ShiftMask,
  'Win': X.Mod4Mask,
  'Mod': X.Mod4Mask,
}

IGNORED_MOD_MASKS = (0, X.LockMask, X.Mod2Mask, X.LockMask | X.Mod2Mask)

load_keysym_group('xf86')

WindowState = namedtuple('State', 'maximized_vert, maximized_horz, undecorated')
'''Window state

Has following attributes:

maximized_vert
  Is window maximized vertically.

maximized_horz
  Is window maximized horizontally.

undecorated
  Is window does not have decorations (openbox specific state).
'''

class RestartException(Exception): pass


class WM(object):
    """Core orcsome instance

    Can be get in any time as::

        import orcsome
        wm = orcsome.get_wm()
    """

    def __init__(self):
        self.rfifo, self.wfifo = os.pipe()
        fl = fcntl.fcntl(self.rfifo, fcntl.F_GETFL)
        fcntl.fcntl(self.rfifo, fcntl.F_SETFL, fl | os.O_NONBLOCK)

        self.key_handlers = {}
        self.property_handlers = {}
        self.create_handlers = []
        self.destroy_handlers = {}
        self.init_handlers = []
        self.deinit_handlers = []
        self.signal_handlers = {}

        self.grab_keyboard_handler = None
        self.grab_pointer_handler = None

        self.focus_history = []

        self.re_cache = {}

        self.dpy = Xlib.display.Display()
        self.root = self.dpy.screen().root

        screen_saver.init(self.dpy)

    def emit(self, signal):
        os.write(self.wfifo, signal + '\n')

    def keycode(self, key):
        sym = string_to_keysym(key)
        if sym is X.NoSymbol:
            logging.getLogger(__name__).error('Invalid key [%s]' % key)
            return None

        return self.dpy.keysym_to_keycode(sym)

    def bind_key(self, window, keydef):
        parts = keydef.split('+')
        mod, key = parts[:-1], parts[-1]
        modmask = 0
        for m in mod:
            try:
                modmask |= MODIFICATORS[m]
            except KeyError:
                logging.getLogger(__name__).error('Invalid key [%s]' % keydef)
                return lambda func: func

        sym = string_to_keysym(key)
        if sym is X.NoSymbol:
            logging.getLogger(__name__).error('Invalid key [%s]' % keydef)
            return lambda func: func

        code = self.dpy.keysym_to_keycode(sym)

        def inner(func):
            keys = []
            wid = window.id
            for imask in IGNORED_MOD_MASKS:
                mask = modmask | imask
                window.grab_key(code, mask, True, X.GrabModeAsync, X.GrabModeAsync)
                self.key_handlers.setdefault(window.id, {})[(mask, code)] = func
                keys.append((mask, code))

            def remove():
                for k in keys:
                    del self.key_handlers[wid][k]

            func.remove = remove
            return func

        return inner

    def on_key(self, *args):
        """Signal decorator to define hotkey

        You can define global key::

           wm.on_key('Alt+Return')(
               spawn('xterm'))

        Or key binded to specific window::

           @wm.on_create(cls='URxvt')
           def bind_urxvt_keys():
               # Custom key to close only urxvt windows
               wm.on_key(wm.event_window, 'Ctrl+d')(
                   close)

        Key defenition is a string in format ``[mod + ... +]keysym`` where ``mod`` is
        one of modificators [Alt, Shift, Control(Ctrl), Mod(Win)] and
        ``keysym`` is a key name.
        """

        if getattr(args[0], 'id', False):
            window = args[0]
            key = args[1]
        else:
            window = self.root
            key = args[0]

        return self.bind_key(window, key)

    def on_create(self, *args, **matchers):
        """Signal decorator to handle window creation

        Can be used in two forms. Listen to any window creation::

           @wm.on_create
           def debug(wm):
               print wm.event_window.get_wm_class()

        Or specific window::

           @wm.on_create(cls='Opera')
           def use_firefox_luke(wm):
               wm.close_window(wm.event_window)
               spawn('firefox')()

        Also, orcsome calls on_create handlers on its startup.
        You can check ``wm.startup`` attribute to denote such event.

        See :meth:`is_match` for ``**matchers`` argument description.
        """

        if args:
            func = args[0]
            self.create_handlers.append(func)

            def remove():
                self.create_handlers.remove(func)

            func.remove = remove
            return func

        def inner(func):
            def match_window():
                if self.is_match(self.event_window, **matchers):
                    func()

            self.create_handlers.append(match_window)

            def remove():
                self.create_handlers.remove(match_window)

            func.remove = remove
            return func

        return inner

    def on_destroy(self, window):
        """Signal decorator to handle window destroy"""

        def inner(func):
            self.destroy_handlers.setdefault(window.id, []).append(func)
            return func

        return inner

    def on_property_change(self, *args):
        """Signal decorator to handle window property change

        One can handle any window property change::

           @wm.on_property_change('_NET_WM_STATE')
           def window_maximized_state_change():
               state = wm.get_window_state(wm.event_window)
               if state.maximized_vert and state.maximized_horz:
                   print 'Look, ma! Window is maximized now!'

        And specific window::

           @wm.on_create
           def switch_to_desktop():
               if not wm.startup:
                   if wm.activate_window_desktop(wm.event_window) is None:
                       # Created window has no any attached desktop so wait for it
                       @wm.on_property_change(wm.event_window, '_NET_WM_DESKTOP')
                       def property_was_set():
                           wm.activate_window_desktop(wm.event_window)
                           property_was_set.remove()

        """
        def inner(func):
            if getattr(args[0], 'id', False):
                wid = args[0].id
                props = args[1:]
            else:
                wid = None
                props = args

            for p in props:
                atom = self.get_atom(p)
                self.property_handlers.setdefault(atom, {}).setdefault(wid, []).append(func)

            def remove():
                for p in props:
                    atom = self.get_atom(p)
                    self.property_handlers[atom][wid].remove(func)

            func.remove = remove
            return func

        return inner

    def get_clients(self):
        """Return wm client list"""

        result = []
        wids = self.root.get_full_property(self.get_atom('_NET_CLIENT_LIST'), Xatom.WINDOW)

        if wids:
            for wid in wids.value:
                result.append(self.dpy.create_resource_object('window', wid))

        return result

    def get_stacked_clients(self):
        """Return client list in stacked order.

        Most top window will be last in list. Can be useful to determine window visibility.
        """

        result = []
        wids = self.root.get_full_property(
            self.get_atom('_NET_CLIENT_LIST_STACKING'), Xatom.WINDOW)

        if wids:
            for wid in wids.value:
                result.append(self.dpy.create_resource_object('window', wid))

        return result

    @property
    def current_window(self):
        """Return currently active (with input focus) window"""
        result = self.root.get_full_property(self.get_atom('_NET_ACTIVE_WINDOW'), Xatom.WINDOW)
        if result:
            return self.dpy.create_resource_object('window', result.value[0])

        return None

    @property
    def current_desktop(self):
        """Return current desktop number

        Counts from zero.
        """
        return self.root.get_full_property(
            self.dpy.intern_atom('_NET_CURRENT_DESKTOP'), 0).value[0]

    def get_window_desktop(self, window):
        """Return window desktop.

        Result is:

        * number from 0 to desktop_count - 1
        * -1 if window placed on all desktops
        * None if window does not have desktop property

        """

        d = self.get_window_property_safe(window, '_NET_WM_DESKTOP', 0)
        if d:
            d = d.value[0]
            if d == 0xffffffff:
                return -1
            else:
                return d

        return None

    def set_current_desktop(self, num):
        """Activate desktop ``num``"""
        if num < 0:
            return

        self._send_event(self.root, self.dpy.intern_atom('_NET_CURRENT_DESKTOP'), [num])
        self.dpy.flush()

    def _send_event(self, window, ctype, data, mask=None):
        data = (data + ([0] * (5 - len(data))))[:5]
        ev = ClientMessage(window=window, client_type=ctype, data=(32, (data)))
        self.root.send_event(ev, event_mask=X.SubstructureRedirectMask)

    def get_window_role(self, window):
        """Return WM_WINDOW_ROLE property"""
        d = self.get_window_property_safe(window, 'WM_WINDOW_ROLE', Xatom.STRING)
        if d is None or d.format != 8:
            return None
        else:
            return d.value

    def get_window_title(self, window):
        """Return _NET_WM_NAME property"""
        d = self.get_window_property_safe(window, '_NET_WM_NAME', self.get_atom('UTF8_STRING'))
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

    def is_match(self, window, name=None, cls=None, role=None, desktop=None, title=None):
        """Check if window suits given matchers.

        Matchers keyword arguments are used in :meth:`on_create`,
        :func:`~orcsome.actions.spawn_or_raise`. :meth:`find_clients` and
        :meth:`find_client`.

        name
          window name (also referenced as `instance`).
          The first part of ``WM_CLASS`` property.

        cls
          window class. The second part of ``WM_CLASS`` property.

        role
          window role. Value of ``WM_WINDOW_ROLE`` property.

        desktop
          matches windows placed on specific desktop. Must be int.

        title
          window title.

        `name`, `cls`, `title` and `role` can be regular expressions.

        """
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

        if match and title:
            match = self.match_string(title, self.get_window_title(window))

        if match and desktop is not None:
            wd = self.get_window_desktop(window)
            match = wd == desktop

        return match

    def find_clients(self, clients, **matchers):
        """Return matching clients list

        :param clients: window list returned by :meth:`get_clients` or :meth:`get_stacked_clients`.
        :param \*\*matchers: keyword arguments defined in :meth:`is_match`
        """
        result = []
        for c in clients:
            if self.is_match(c, **matchers):
                result.append(c)

        return result

    def find_client(self, clients, **matchers):
        """Return first matching client

        :param clients: window list returned by :meth:`get_clients` or :meth:`get_stacked_clients`.
        :param \*\*matchers: keyword arguments defined in :meth:`is_match`
        """
        result = self.find_clients(clients, **matchers)
        try:
            return result[0]
        except IndexError:
            return None

    def process_create_window(self, window):
        window.change_attributes(event_mask=X.StructureNotifyMask |
            X.PropertyChangeMask | X.FocusChangeMask)

        self.event_window = window
        for handler in self.create_handlers:
            handler()

    def run(self):
        self.root.change_attributes(event_mask=X.SubstructureNotifyMask)

        for h in self.init_handlers:
            h()

        self.startup = True
        for c in self.get_clients():
            self.process_create_window(c)

    def handle_keypress(self, event):
        if self.grab_keyboard_handler:
            self.grab_keyboard_handler(True, event.state, event.detail)
        else:
            try:
                handler = self.key_handlers[event.window.id][(event.state, event.detail)]
            except KeyError:
                pass
            else:
                self.event = event
                self.event_window = event.window
                handler()

    def handle_keyrelease(self, event):
        if self.grab_keyboard_handler:
            self.grab_keyboard_handler(False, event.state, event.detail)

    def handle_create(self, event):
        self.event = event
        self.startup = False
        self.process_create_window(event.window)

    def handle_destroy(self, event):
        try:
            handlers = self.destroy_handlers[event.window.id]
        except KeyError:
            pass
        else:
            self.event = event
            self.event_window = event.window
            for h in handlers:
                h()
        finally:
            self._clean_window_data(event.window)

    def handle_property(self, event):
        atom = event.atom
        if event.state == 0 and atom in self.property_handlers:
            wphandlers = self.property_handlers[atom]
            self.event_window = event.window
            self.event = event
            if event.window.id in wphandlers:
                for h in wphandlers[event.window.id]:
                    h()

            if None in wphandlers:
                for h in wphandlers[None]:
                    h()

    def handle_focusin(self, event):
        try:
            self.focus_history.remove(event.window)
        except ValueError:
            pass

        self.focus_history.append(event.window)


    def handle_events(self):
        handlers = {
            X.KeyPress: self.handle_keypress,
            X.KeyRelease: self.handle_keyrelease,
            X.CreateNotify: self.handle_create,
            X.DestroyNotify: self.handle_destroy,
            X.FocusIn: self.handle_focusin,
            X.PropertyNotify: self.handle_property,
        }

        while True:
            try:
                readable, _, _ = select([self.dpy, self.rfifo], [], [])
            except KeyboardInterrupt:
                return True

            if not readable:
                continue

            if self.dpy in readable:
                while True:
                    try:
                        i = self.dpy.pending_events()
                    except KeyboardInterrupt:
                        return True

                    if not i:
                        break

                    while i > 0:
                        event = self.dpy.next_event()
                        i = i - 1

                        try:
                            h = handlers[event.type]
                        except KeyError:
                            continue

                        try:
                            h(event)
                        except (KeyboardInterrupt, SystemExit):
                            return True
                        except RestartException:
                            return False
                        except:
                            import logging
                            logging.getLogger(__name__).exception('Boo')

            if self.rfifo in readable:
                for s in os.read(self.rfifo, 8192).splitlines():
                    if s in self.signal_handlers:
                        for h in self.signal_handlers[s]:
                            try:
                                h()
                            except (KeyboardInterrupt, SystemExit):
                                return True
                            except RestartException:
                                return False
                            except:
                                import logging
                                logging.getLogger(__name__).exception('Boo')


    def _clean_window_data(self, window):
        wid = window.id
        if wid in self.key_handlers:
            del self.key_handlers[wid]

        if wid in self.destroy_handlers:
            self.destroy_handlers[wid]

        try:
            self.focus_history.remove(window)
        except ValueError:
            pass

        for atom, whandlers in self.property_handlers.items():
            if wid in whandlers:
                del whandlers[wid]

            if not self.property_handlers[atom]:
                del self.property_handlers[atom]

    def focus_window(self, window):
        """Activate window"""
        self._send_event(window, self.get_atom("_NET_ACTIVE_WINDOW"), [2, X.CurrentTime])
        self.dpy.flush()

    def focus_and_raise(self, window):
        """Activate window desktop, set input focus and raise it"""
        self.activate_window_desktop(window)
        window.configure(stack_mode=X.Above)
        self.focus_window(window)

    def place_window_above(self, window):
        """Float up window in wm stack"""
        window.configure(stack_mode=X.Above)
        self.dpy.flush()

    def place_window_below(self, window):
        """Float down window in wm stack"""
        window.configure(stack_mode=X.Below)
        self.dpy.flush()

    def activate_window_desktop(self, window):
        """Activate window desktop

        Return:

        * True if window is placed on different from current desktop
        * False if window desktop is the same
        * None if window does not have desktop property
        """
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
        """Return atom value"""
        return self.dpy.get_atom(atom_name)

    def get_atom_name(self, atom):
        """Return atom string representation"""
        return self.dpy.get_atom_name(atom)

    def get_window_state(self, window):
        """Return :class:`WindowState` instance"""
        state = self.get_window_property_safe(window, '_NET_WM_STATE', Xatom.ATOM)

        return WindowState(
            state and self.get_atom('_NET_WM_STATE_MAXIMIZED_VERT') in state.value,
            state and self.get_atom('_NET_WM_STATE_MAXIMIZED_HORZ') in state.value,
            state and self.get_atom('_OB_WM_STATE_UNDECORATED') in state.value
        )

    def decorate_window(self, window, decorate=True):
        """Decorate/undecorate window

        :param decorate: undecorate window if False

        .. note::
            Openbox specific.
        """
        state_atom = self.get_atom('_NET_WM_STATE')
        undecorated_atom = self.get_atom('_OB_WM_STATE_UNDECORATED')
        self._send_event(window, state_atom, [int(not decorate), undecorated_atom])
        self.dpy.flush()

    def close_window(self, window):
        """Send request to wm to close window"""
        self._send_event(window, self.get_atom("_NET_CLOSE_WINDOW"), [X.CurrentTime])
        self.dpy.flush()

    def change_window_desktop(self, window, desktop):
        """Move window to ``desktop``"""
        if desktop < 0:
            return

        self._send_event(window, self.get_atom("_NET_WM_DESKTOP"), [desktop])
        self.dpy.flush()

    def stop(self, is_exit=False):
        self.key_handlers.clear()
        self.property_handlers.clear()
        self.create_handlers[:] = []
        self.destroy_handlers.clear()
        self.focus_history[:] = []

        self.signal_handlers.clear()

        if not is_exit:
            self.root.ungrab_key(X.AnyKey, X.AnyModifier)
            for c in self.get_clients():
                c.ungrab_key(X.AnyKey, X.AnyModifier)

        for h in self.deinit_handlers:
            try:
                h()
            except:
                logging.getLogger(__name__).exception('Shutdown error')

        self.init_handlers[:] = []
        self.deinit_handlers[:] = []

    def grab_keyboard(self, func):
        if self.grab_keyboard_handler:
            return False

        result = self.root.grab_keyboard(False, X.GrabModeAsync, X.GrabModeAsync, X.CurrentTime)
        if result == 0:
            self.grab_keyboard_handler = func
            return True

        return False

    def ungrab_keyboard(self):
        self.grab_keyboard_handler = None
        self.dpy.ungrab_keyboard(X.CurrentTime)

    def grab_pointer(self, func, mask=None):
        if self.grab_pointer_handler:
            return False

        result = self.root.grab_pointer(False, 0, X.GrabModeAsync, X.GrabModeAsync,
            X.NONE, X.NONE, X.CurrentTime)

        if result == 0:
            self.grab_pointer_handler = func
            return True

        return False

    def ungrab_pointer(self):
        self.grab_pointer_handler = None
        self.dpy.ungrab_pointer(X.CurrentTime)

    def on_init(self, func):
        self.init_handlers.append(func)
        return func

    def on_deinit(self, func):
        self.deinit_handlers.append(func)
        return func

    def on_signal(self, signal):
        def inner(func):
            self.signal_handlers.setdefault(signal, []).append(func)

            def remove():
                self.signal_handlers[signal].remove(func)

            func.remove = remove
            return func

        return inner

    def get_window_property_safe(self, window, atom_name, ptype):
        try:
            return window.get_full_property(self.get_atom(atom_name), ptype)
        except BadWindow:
            return None


class TestWM(object):
    def on_key(self, key):
        assert isinstance(key, basestring), 'First argument to on_key must be string'
        return lambda func: func

    def on_create(self, *args, **matchers):
        assert matchers or args

        if args:
            assert len(args) == 1
            return args[0]

        if matchers:
            possible_args = set(('cls', 'role', 'name', 'desktop'))
            assert possible_args.union(matchers) == possible_args, \
                'Invalid matcher, must be one of %s' % possible_args

        return lambda func: func

    def on_property_change(self, *args):
        assert all(isinstance(r, basestring) for r in args)
        return lambda func: func

    def on_destroy(self, window):
        return lambda func: func

    def on_init(self, func):
        return func

    def on_deinit(self, func):
        return func
