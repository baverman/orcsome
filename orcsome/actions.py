import time
import os

from orcsome import get_wm

_create_spawn_queue = []

def _create_spawn_hook():
    if not _create_spawn_queue:
        return

    wm = get_wm()
    t = time.time() - 100 # 100 seconds must be enough to start any heavy app
    for r in _create_spawn_queue[:]:
        st, handler, cw, cd, matchers = r
        if st < t:
            _create_spawn_queue.remove(r)
        elif wm.is_match(wm.event_window, **matchers):
            _create_spawn_queue.remove(r)
            handler(cd, cw)

def spawn(cmd, switch_to_desktop=None):
    """Run specified cmd

    :param cmd: shell command. Can include pipes, redirection and so on.
    :param switch_to_desktop: integer. Desktop number to activate after command start.
       Starts from zero.
    """
    def inner():
        _spawn(cmd)
        if switch_to_desktop is not None:
            get_wm().set_current_desktop(switch_to_desktop)

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
    def inner():
        wm = get_wm()
        client = wm.find_client(wm.get_clients(), **matchers)
        if client:
            if bring_to_current:
                wm.change_window_desktop(client, wm.current_desktop)

            wm.focus_and_raise(client)
        else:
            if on_create:
                if not _create_spawn_hook in wm.create_handlers:
                    wm.on_create(_create_spawn_hook)

                _create_spawn_queue.append((
                    time.time(), on_create, wm.current_window, wm.current_desktop, matchers))

            spawn(cmd, switch_to_desktop)()

    return inner

def _focus(window, direction):
    wm = get_wm()
    clients = wm.find_clients(wm.get_clients(), desktop=wm.get_window_desktop(window))
    idx = clients.index(window)
    newc = clients[(idx + direction) % len(clients)]
    wm.focus_and_raise(newc)

def focus_next(window=None):
    """Focus next client on current desktop.

    next/prev are defined by client creation time
    """
    _focus(window or get_wm().current_window, 1)

def focus_prev(window=None):
    """Focus previous client on current desktop.

    next/prev are defined by client creation time
    """
    _focus(window or get_wm().current_window, -1)

def close(window=None):
    """Close window"""
    get_wm().close_window(window or get_wm().current_window)

def _spawn(cmd):
    pid = os.fork()
    if pid != 0:
        os.waitpid(pid, 0)
        return

    os.setsid()

    pid = os.fork()
    if pid != 0:
        os._exit(0)

    try:
        os.execv(os.environ.get('SHELL', '/bin/sh'), ['shell', '-c', cmd])
    except Exception:
        os._exit(255)

def restart():
    """Restart orcsome"""
    from .core import RestartException
    raise RestartException()