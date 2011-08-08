import time

_create_spawn_queue = []

def _create_spawn_hook(wm):
    if not _create_spawn_queue:
        return

    t = time.time() - 100 # 100 seconds must be enough to start any heavy app
    for r in _create_spawn_queue[:]:
        st, handler, cw, cd, matchers = r
        if st < t:
            _create_spawn_queue.remove(r)
        elif wm.is_match(wm.event_window, **matchers):
            _create_spawn_queue.remove(r)
            handler(wm, cd, cw)
_create_spawn_hook.installed = False

def spawn(cmd, switch_to_desktop=None):
    """Run specified cmd

    :param cmd: shell command. Can include pipes, redirection and so on.
    :param switch_to_desktop: integer. Desktop number to activate after command start.
       Starts from zero.
    """
    def inner(wm):
        import subprocess
        subprocess.Popen(cmd, shell=True)
        if switch_to_desktop is not None:
            wm.set_current_desktop(switch_to_desktop)

    return inner

def spawn_or_raise(cmd, switch_to_desktop=None, bring_to_current=False, on_create=None, **matchers):
    """Activate window or run command

    Activation means to give input focus for existing window matched by provided rules.

    ``switch_to_desktop`` controls appear of spawned windows and ``bring_to_current``
    change matched windows behavior.

    ``on_create`` is a function with the following signature::

       def on_spawned_window_create(wm, desktop, window)

    Where ``wm`` is :class:`orcsome instance <orcsome.core.WM>`, ``desktop`` and ``window``
    are active desktop and focused window before spawn_or_raise call.

    :param cmd: same as in :func:`spawn`.
    :param switch_to_desktop: same as in :func:`spawn`.
    :param bring_to_current: if True, move matched window to current desktop
    :param on_create: on create handler, called after command spawn
    :param \*\*matchers: see :meth:`~orcsome.core.WM.is_match`
    """
    def inner(wm):
        client = wm.find_client(wm.get_clients(), **matchers)
        if client:
            wm.focus_and_raise(client)
        else:
            if on_create:
                if not _create_spawn_hook.installed:
                    wm.on_create(_create_spawn_hook)
                    _create_spawn_hook.installed = True

                _create_spawn_queue.append((
                    time.time(), on_create, wm.current_window, wm.current_desktop, matchers))

            spawn(cmd, switch_to_desktop)(wm)

    return inner

def focus_next(wm, c=None):
    """Focus next client on current desktop.

    next/prev are defined by client creation time
    """

    c = c or wm.event_window
    clients = wm.find_clients(wm.get_clients(), desktop=wm.get_window_desktop(c))
    idx = clients.index(c)
    newc = clients[(idx + 1) % len(clients)]
    wm.focus_and_raise(newc)

def focus_prev(wm, c=None):
    """Focus previous client on current desktop.

    next/prev are defined by client creation time
    """

    c = c or wm.event_window
    clients = wm.find_clients(wm.get_clients(), desktop=wm.get_window_desktop(c))
    idx = clients.index(c)
    newc = clients[(idx - 1) % len(clients)]
    wm.focus_and_raise(newc)
