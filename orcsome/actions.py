import time

from . import utils
from .wm import RestartException

class Actions(object):
    def __init__(self):
        self.spawn_queue = []

    def create_spawn_hook(self):
        if not self.spawn_queue:
            return

        t = time.time() - 100 # 100 seconds must be enough to start any heavy app
        for r in self.spawn_queue[:]:
            st, handler, cw, cd, matchers = r
            if st < t:
                self.spawn_queue.remove(r)
            elif self.event_window.matches(**matchers):
                self.spawn_queue.remove(r)
                handler(cd, self.window(cw))

    def spawn(self, cmd, switch_to_desktop=None):
        """Run specified cmd

        :param cmd: shell command. Can include pipes, redirection and so on.
        :param switch_to_desktop: integer. Desktop number to activate after
           command start. Starts from zero.
        """
        utils.spawn(cmd)
        if switch_to_desktop is not None:
            self.activate_desktop(switch_to_desktop)

    def spawn_or_raise(self, cmd, switch_to_desktop=None, bring_to_current=False,
            on_create=None, **matchers):
        """Activate window or run command

        Activation means to give input focus for existing window matched
        by provided rules.

        ``switch_to_desktop`` controls appear of spawned windows and
        ``bring_to_current`` change matched windows behavior.

        ``on_create`` is a function with the following signature::

           def on_spawned_window_create(wm, desktop, window)

        Where ``wm`` is :class:`orcsome instance <orcsome.core.WM>`,
        ``desktop`` and ``window`` are active desktop and focused
        window before spawn_or_raise call.

        :param cmd: same as in :func:`spawn`.
        :param switch_to_desktop: same as in :func:`spawn`.
        :param bring_to_current: if True, move matched window to current desktop
        :param on_create: on create handler, called after command spawn
        :param \*\*matchers: see :meth:`~orcsome.core.WM.is_match`
        """
        client = self.find_client(self.get_clients(), **matchers)
        if client:
            if bring_to_current and self.current_desktop != client.desktop:
                @self.on_property_change(client, '_NET_WM_DESKTOP')
                def focus_and_raise_cb():
                    focus_and_raise_cb.remove()
                    self.focus_and_raise(self.event_window)

                self.change_window_desktop(client, self.current_desktop)
            else:
                self.focus_and_raise(client)
        else:
            if on_create:
                if not self.create_spawn_hook in self.create_handlers:
                    self.on_create(self.create_spawn_hook)

                self.spawn_queue.append((time.time(), on_create,
                    int(self.current_window), self.current_desktop, matchers))

            self.spawn(cmd, switch_to_desktop)

    def _focus(self, window, direction):
        clients = self.find_clients(self.get_clients(), desktop=window.desktop)
        idx = clients.index(window)
        newc = clients[(idx + direction) % len(clients)]
        self.focus_and_raise(newc)

    def focus_next(self, window=None):
        """Focus next client on current desktop.

        next/prev are defined by client creation time
        """
        self._focus(window or self.current_window, 1)

    def focus_prev(self, window=None):
        """Focus previous client on current desktop.

        next/prev are defined by client creation time
        """
        self._focus(window or self.current_window, -1)

    def restart(self):
        """Restart orcsome"""
        raise RestartException()

    def do(self, callable, *args, **kwargs):
        callable(*args, **kwargs)

    def activate_window_desktop(self, window):
        """Activate window desktop

        Return:

        * True if window is placed on different from current desktop
        * False if window desktop is the same
        * None if window does not have desktop property
        """
        wd = window.desktop
        if wd is not None:
            if self.current_desktop != wd:
                self.activate_desktop(wd)
                return True
            else:
                return False
        else:
            return None

