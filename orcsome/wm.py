import os
import logging

from . import xlib as X, ev
from .wrappers import Window
from .aliases import KEYS as KEY_ALIASES
from .utils import Mixable, ActionCaller

logger = logging.getLogger(__name__)

MODIFICATORS = {
  'Alt': X.Mod1Mask,
  'Control': X.ControlMask,
  'Ctrl': X.ControlMask,
  'Shift': X.ShiftMask,
  'Win': X.Mod4Mask,
  'Mod': X.Mod4Mask,
  'Hyper': X.Mod4Mask,
  'Super': X.Mod4Mask,
}

IGNORED_MOD_MASKS = (0, X.LockMask, X.Mod2Mask, X.LockMask | X.Mod2Mask)


class RestartException(Exception): pass


class WM(Mixable):
    """Core orcsome instance

    Can be get in any time as::

        import orcsome
        wm = orcsome.get_wm()
    """

    def __init__(self, loop):
        self.handlers = {
            X.KeyPress: self.handle_keypress,
            X.KeyRelease: self.handle_keyrelease,
            X.CreateNotify: self.handle_create,
            X.DestroyNotify: self.handle_destroy,
            X.FocusIn: self.handle_focus,
            X.FocusOut: self.handle_focus,
            X.PropertyNotify: self.handle_property,
        }
        self._event = X.ffi.new('XEvent *')

        self.key_handlers = {}
        self.property_handlers = {}
        self.create_handlers = []
        self.destroy_handlers = {}
        self.init_handlers = []
        self.deinit_handlers = []
        self.timer_handlers = []

        self.grab_keyboard_handler = None
        self.grab_pointer_handler = None

        self.focus_history = []

        self.dpy = X.XOpenDisplay(X.NULL)
        if self.dpy == X.NULL:
            raise Exception("Can't open display")

        self.fd = X.ConnectionNumber(self.dpy)
        self.root = X.DefaultRootWindow(self.dpy)
        self.atom = X.AtomCache(self.dpy)

        self.undecorated_atom_name = '_OB_WM_STATE_UNDECORATED'
        self.track_kbd_layout = False

        self.loop = loop
        self.xevent_watcher = ev.IOWatcher(self._xevent_cb, self.fd, ev.EV_READ)
        self.xevent_watcher.start(self.loop)

        self.restart_handler = None

    def window(self, window_id):
        window = Window(window_id)
        window.wm = self
        return window

    def emit(self, signal):
        os.write(self.wfifo, signal + '\n')

    def keycode(self, key):
        sym = X.XStringToKeysym(KEY_ALIASES.get(key, key))
        if sym is X.NoSymbol:
            return None

        return X.XKeysymToKeycode(self.dpy, sym)

    def parse_keydef(self, keydef):
        keys = [r.strip() for r in keydef.split()]
        result = []
        for k in keys:
            parts = k.split('+')
            mod, key = parts[:-1], parts[-1]
            modmask = 0
            for m in mod:
                try:
                    modmask |= MODIFICATORS[m]
                except KeyError:
                    return None

            code = self.keycode(key)
            if not code:
                return None

            result.append((code, modmask))

        return result

    def bind_key(self, window, keydef):
        code_mmask_list = self.parse_keydef(keydef)
        if not code_mmask_list:
            logger.error('Invalid key definition [%s]' % keydef)
            return ActionCaller(self, lambda func: func)

        if len(code_mmask_list) == 1:
            code, modmask = code_mmask_list[0]

            def inner(func):
                keys = []
                for imask in IGNORED_MOD_MASKS:
                    mask = modmask | imask
                    X.XGrabKey(self.dpy, code, mask, window, True, X.GrabModeAsync, X.GrabModeAsync)
                    self.key_handlers.setdefault(window, {})[(mask, code)] = func
                    keys.append((mask, code))

                def remove():
                    for k in keys:
                        del self.key_handlers[window][k]

                func.remove = remove
                return func

            return ActionCaller(self, inner)
        else:
            return ActionCaller(self, lambda func: func)

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

        if isinstance(args[0], Window):
            window = args[0]
            key = args[1]
        else:
            window = self.root
            key = args[0]

        return self.bind_key(window, key)

    def _on_create_manage(self, ignore_startup, *args, **matchers):
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
        def inner(func):
            if matchers:
                ofunc = func
                func = lambda: self.event_window.matches(**matchers) and ofunc()

            if ignore_startup:
                oofunc = func
                func = lambda: self.startup or oofunc()

            self.create_handlers.append(func)

            def remove():
                self.create_handlers.remove(func)

            func.remove = remove
            return func

        if args:
            return inner(args[0])
        else:
            return ActionCaller(self, inner)

    def on_create(self, *args, **matchers):
        return self._on_create_manage(True, *args, **matchers)

    def on_manage(self, *args, **matchers):
        return self._on_create_manage(False, *args, **matchers)

    def on_destroy(self, window):
        """Signal decorator to handle window destroy"""

        def inner(func):
            self.destroy_handlers.setdefault(window, []).append(func)
            return func

        return ActionCaller(self, inner)

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
            if isinstance(args[0], Window):
                window = args[0]
                props = args[1:]
            else:
                window = None
                props = args

            for p in props:
                atom = self.atom[p]
                self.property_handlers.setdefault(
                    atom, {}).setdefault(window, []).append(func)

            def remove():
                for p in props:
                    atom = self.atom[p]
                    self.property_handlers[atom][window].remove(func)

            func.remove = remove
            return func

        return ActionCaller(self, inner)

    def on_timer(self, timeout, start=True, first_timeout=None):
        def inner(func):
            def cb(l, w, e):
                if func():
                    timer.stop(self.loop)
                else:
                    timer.update_next_stop()

            self.timer_handlers.append(func)

            timer = ev.TimerWatcher(cb, first_timeout or timeout, timeout)
            func.start = lambda after=None, repeat=None: timer.start(self.loop, after, repeat)
            func.stop = lambda: timer.stop(self.loop)
            func.again = lambda: timer.again(self.loop)
            func.remaining = lambda: timer.remaining(self.loop)
            func.overdue = lambda timeout: timer.overdue(timeout)

            if start:
                func.start()

            return func

        return ActionCaller(self, inner)

    def get_clients(self, ids=False):
        """Return wm client list"""
        result = X.get_window_property(self.dpy, self.root,
            self.atom['_NET_CLIENT_LIST'], self.atom['WINDOW']) or []

        if not ids:
            result = [self.window(r) for r in result]

        return result

    def get_stacked_clients(self):
        """Return client list in stacked order.

        Most top window will be last in list. Can be useful to determine window visibility.
        """
        return X.get_window_property(self.dpy, self.root,
            self.atom['_NET_CLIENT_LIST_STACKING'], self.atom['WINDOW']) or []

    @property
    def current_window(self):
        """Return currently active (with input focus) window"""
        result = X.get_window_property(self.dpy, self.root,
            self.atom['_NET_ACTIVE_WINDOW'], self.atom['WINDOW'])

        if result:
            return self.window(result[0])

    @property
    def current_desktop(self):
        """Return current desktop number

        Counts from zero.
        """
        return X.get_window_property(self.dpy, self.root,
            self.atom['_NET_CURRENT_DESKTOP'])[0]

    def activate_desktop(self, num):
        """Activate desktop ``num``"""
        if num < 0:
            return

        self._send_event(self.root, self.atom['_NET_CURRENT_DESKTOP'], [num])
        self._flush()

    def _send_event(self, window, mtype, data):
        data = (data + ([0] * (5 - len(data))))[:5]
        ev = X.ffi.new('XClientMessageEvent *', {
            'type': X.ClientMessage,
            'window': window,
            'message_type': mtype,
            'format': 32,
            'data': {'l': data},
        })
        X.XSendEvent(self.dpy, self.root, False, X.SubstructureRedirectMask,
            X.ffi.cast('XEvent *', ev))

    def _flush(self):
        X.XFlush(self.dpy)

    def find_clients(self, clients, **matchers):
        """Return matching clients list

        :param clients: window list returned by :meth:`get_clients` or :meth:`get_stacked_clients`.
        :param \*\*matchers: keyword arguments defined in :meth:`is_match`
        """
        return [r for r in clients if r.matches(**matchers)]

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
        X.XSelectInput(self.dpy, window, X.StructureNotifyMask |
                       X.PropertyChangeMask | X.FocusChangeMask)

        self.event_window = window
        for handler in self.create_handlers:
            handler()

    def init(self):
        X.XSelectInput(self.dpy, self.root, X.SubstructureNotifyMask)

        for h in self.init_handlers:
            h()

        self.startup = True
        for c in self.get_clients():
            self.process_create_window(c)

        X.XSync(self.dpy, False)

        X.XSetErrorHandler(error_handler)

    def handle_keypress(self, event):
        event = event.xkey
        if self.grab_keyboard_handler:
            self.grab_keyboard_handler(True, event.state, event.keycode)
        else:
            try:
                handler = self.key_handlers[event.window][(event.state, event.keycode)]
            except KeyError:
                pass
            else:
                self.event = event
                self.event_window = self.window(event.window)
                handler()

    def handle_keyrelease(self, event):
        event = event.xkey
        if self.grab_keyboard_handler:
            self.grab_keyboard_handler(False, event.state, event.keycode)

    def handle_create(self, event):
        event = event.xcreatewindow
        self.event = event
        self.startup = False
        self.process_create_window(self.window(event.window))

    def handle_destroy(self, event):
        event = event.xdestroywindow
        try:
            handlers = self.destroy_handlers[event.window]
        except KeyError:
            pass
        else:
            self.event = event
            self.event_window = self.window(event.window)
            for h in handlers:
                h()
        finally:
            self._clean_window_data(event.window)

    def handle_property(self, event):
        event = event.xproperty
        atom = event.atom
        if event.state == 0 and atom in self.property_handlers:
            wphandlers = self.property_handlers[atom]
            self.event_window = self.window(event.window)
            self.event = event
            if event.window in wphandlers:
                for h in wphandlers[event.window]:
                    h()

            if None in wphandlers:
                for h in wphandlers[None]:
                    h()

    def handle_focus(self, event):
        event = event.xfocus
        if event.type == X.FocusIn:
            try:
                self.focus_history.remove(event.window)
            except ValueError:
                pass

            self.focus_history.append(event.window)
            if event.mode in (0, 3) and self.track_kbd_layout:
                prop = X.get_window_property(self.dpy, event.window, self.atom['_ORCSOME_KBD_GROUP'])
                if prop:
                    X.set_kbd_group(self.dpy, prop[0])
                else:
                    X.set_kbd_group(self.dpy, 0)
        else:
            if event.mode in (0, 3) and self.track_kbd_layout:
                X.set_window_property(self.dpy, event.window, self.atom['_ORCSOME_KBD_GROUP'],
                                      self.atom['CARDINAL'], 32, [X.get_kbd_group(self.dpy)])

    def _xevent_cb(self, loop, watcher, events):
        event = self._event
        while True:
            i = X.XPending(self.dpy)
            if not i: break

            while i > 0:
                X.XNextEvent(self.dpy, event)
                i -= 1

                try:
                    h = self.handlers[event.type]
                except KeyError:
                    continue

                try:
                    h(event)
                except RestartException:
                    if self.restart_handler:
                        self.restart_handler()
                        return
                except:
                    logger.exception('Boo')

    def _clean_window_data(self, window):
        if window in self.key_handlers:
            del self.key_handlers[window]

        if window in self.destroy_handlers:
            self.destroy_handlers[window]

        try:
            self.focus_history.remove(window)
        except ValueError:
            pass

        for atom, whandlers in self.property_handlers.items():
            if window in whandlers:
                del whandlers[window]

            if not self.property_handlers[atom]:
                del self.property_handlers[atom]

    def focus_window(self, window):
        """Activate window"""
        self._send_event(window, self.atom['_NET_ACTIVE_WINDOW'], [2, X.CurrentTime])
        self._flush()

    def focus_and_raise(self, window):
        """Activate window desktop, set input focus and raise it"""
        self.activate_window_desktop(window)
        X.XConfigureWindow(self.dpy, window, X.CWStackMode,
            X.ffi.new('XWindowChanges *', {'stack_mode': X.Above}))
        self.focus_window(window)

    def place_window_above(self, window):
        """Float up window in wm stack"""
        X.XConfigureWindow(self.dpy, window, X.CWStackMode,
            X.ffi.new('XWindowChanges *', {'stack_mode': X.Above}))
        self._flush()

    def place_window_below(self, window):
        """Float down window in wm stack"""
        X.XConfigureWindow(self.dpy, window, X.CWStackMode,
            X.ffi.new('XWindowChanges *', {'stack_mode': X.Below}))
        self._flush()

    def _change_window_hidden_state(self, window, p):
        """Minize window"""
        params = p, self.atom['_NET_WM_STATE_HIDDEN']
        self._send_event(window, self.atom['_NET_WM_STATE'], list(params))
        self._flush()

    def minimize_window(self, window):
        """Minize window"""
        self._change_window_hidden_state(window, 1)

    def restore_window(self, window):
        """Restore window"""
        self._change_window_hidden_state(window, 0)

    def set_window_state(self, window, taskbar=None, pager=None,
            decorate=None, otaskbar=None, vmax=None, hmax=None):
        """Set window state"""
        state_atom = self.atom['_NET_WM_STATE']

        if decorate is not None:
            params = not decorate, self.atom[self.undecorated_atom_name]
            self._send_event(window, state_atom, list(params))

        if taskbar is not None:
            params = not taskbar, self.atom['_NET_WM_STATE_SKIP_TASKBAR']
            self._send_event(window, state_atom, list(params))

        if vmax is not None and vmax == hmax:
            params = vmax, self.atom['_NET_WM_STATE_MAXIMIZED_VERT'], \
                self.atom['_NET_WM_STATE_MAXIMIZED_HORZ']
            self._send_event(window, state_atom, list(params))

        if otaskbar is not None:
            params = [] if otaskbar else [self.atom['_ORCSOME_SKIP_TASKBAR']]
            X.set_window_property(self.dpy, window, self.atom['_ORCSOME_STATE'],
                self.atom['ATOM'], 32, params)

        if pager is not None:
            params = not pager, self.atom['_NET_WM_STATE_SKIP_PAGER']
            self._send_event(window, state_atom, list(params))

        self._flush()


    def get_window_geometry(self, window):
        """Get window geometry

        Returns window geometry without decorations"""
        root_ret = X.ffi.new('Window *')
        x = X.ffi.new('int *')
        y = X.ffi.new('int *')
        w = X.ffi.new('unsigned int *')
        h = X.ffi.new('unsigned int *')
        border_width = X.ffi.new('unsigned int *')
        depth = X.ffi.new('unsigned int *')
        X.XGetGeometry(self.dpy, window, root_ret, x, y, w, h, border_width, depth)
        return x[0], y[0], w[0], h[0]

    def get_screen_size(self):
        """Get size of screen (root window)"""
        return self.get_window_geometry(self.root)[2:]

    def get_workarea(self, desktop=None):
        """Get workarea geometery

        :param desktop: Desktop for working area receiving. If None then current_desktop is using"""
        result = X.get_window_property(self.dpy, self.root,
                                       self.atom['_NET_WORKAREA'], self.atom['CARDINAL'])
        if desktop is None:
            desktop = self.current_desktop
        return result[4*desktop:4*desktop+4]

    def moveresize_window(self, window, x=None, y=None, w=None, h=None):
        """Change window geometry"""
        flags = 0
        flags |= 2 << 12
        if x is not None:
            flags |= 1 << 8
        if y is not None:
            flags |= 1 << 9
        if w is not None:
            flags |= 1 << 10
        if h is not None:
            flags |= 1 << 11
        # Workarea offsets
        o_x, o_y, _, _ = tuple(self.get_workarea())
        params = flags, x+o_x, y+o_y, max(1, w), max(1, h)
        self._send_event(window, self.atom['_NET_MOVERESIZE_WINDOW'], list(params))

    def close_window(self, window=None):
        """Send request to wm to close window"""
        window = window or self.current_window
        if not window: return
        self._send_event(window, self.atom['_NET_CLOSE_WINDOW'], [X.CurrentTime])
        self._flush()

    def change_window_desktop(self, window, desktop):
        """Move window to ``desktop``"""
        if desktop < 0:
            return

        self._send_event(window, self.atom['_NET_WM_DESKTOP'], [desktop])
        self._flush()

    def stop(self, is_exit=False):
        self.key_handlers.clear()
        self.property_handlers.clear()
        self.create_handlers[:] = []
        self.destroy_handlers.clear()
        self.focus_history[:] = []

        if not is_exit:
            X.XUngrabKey(self.dpy, X.AnyKey, X.AnyModifier, self.root)
            for window in self.get_clients():
                X.XUngrabKey(self.dpy, X.AnyKey, X.AnyModifier, window)

        for h in self.timer_handlers:
            h.stop()
        self.timer_handlers[:] = []

        for h in self.deinit_handlers:
            try:
                h()
            except:
                logger.exception('Shutdown error')

        self.init_handlers[:] = []
        self.deinit_handlers[:] = []

    def grab_keyboard(self, func):
        if self.grab_keyboard_handler:
            return False

        result = X.XGrabKeyboard(self.dpy, self.root, False, X.GrabModeAsync,
            X.GrabModeAsync, X.CurrentTime)

        if result == 0:
            self.grab_keyboard_handler = func
            return True

        return False

    def ungrab_keyboard(self):
        self.grab_keyboard_handler = None
        return X.XUngrabKeyboard(self.dpy, X.CurrentTime)

    def grab_pointer(self, func):
        if self.grab_pointer_handler:
            return False

        result = X.XGrabPointer(self.dpy, self.root, False, 0,
            X.GrabModeAsync, X.GrabModeAsync, X.NONE, X.NONE, X.CurrentTime)

        if result == 0:
            self.grab_pointer_handler = func
            return True

        return False

    def ungrab_pointer(self):
        self.grab_pointer_handler = None
        return X.XUngrabPointer(self.dpy, X.CurrentTime)

    def on_init(self, func):
        self.init_handlers.append(func)
        return func

    def on_deinit(self, func):
        self.deinit_handlers.append(func)
        return func

    def get_screen_saver_info(self):
        result = X.ffi.new('XScreenSaverInfo *')
        X.XScreenSaverQueryInfo(self.dpy, self.root, result)
        return result

    def reset_dpms(self):
        power = X.ffi.new('unsigned short *')
        state = X.ffi.new('unsigned char *')
        if X.DPMSInfo(self.dpy, power, state):
            if state[0]:
                X.DPMSDisable(self.dpy)
                X.DPMSEnable(self.dpy)


class ImmediateWM(WM):
    def __init__(self):
        self.dpy = X.XOpenDisplay(X.NULL)
        if self.dpy == X.NULL:
            raise Exception("Can't open display")

        self.root = X.DefaultRootWindow(self.dpy)
        self.atom = X.AtomCache(self.dpy)
        self.undecorated_atom_name = '_OB_WM_STATE_UNDECORATED'


@X.ffi.callback('XErrorHandler')
def error_handler(display, error):
    msg = X.ffi.new('char[100]')
    X.XGetErrorText(display, error.error_code, msg, 100)
    logger.error('{} ({}:{})'.format(X.ffi.string(msg),
        error.request_code, error.minor_code))
    return 0
