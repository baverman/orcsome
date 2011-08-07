import time

def _create_spawn_hook(wm):
    if not _create_spawn_queue:
        return

    t = time.time() - 2
    _create_spawn_queue[:] = [r for r in _create_spawn_queue if r[0] > t]
    for _, handler, cw, matchers in _create_spawn_queue:
        if wm.is_match(wm.event_window, **matchers):
            handler(wm, cw)

_create_spawn_hook.installed = False
_create_spawn_queue = []

def spawn(cmd, switch_to_desktop=None):
    def inner(wm):
        import subprocess
        subprocess.Popen(cmd, shell=True)
        if switch_to_desktop is not None:
            wm.set_current_desktop(switch_to_desktop)

    return inner

def spawn_or_raise(cmd, switch_to_desktop=None, on_create=None, **matchers):
    def inner(wm):
        clients = wm.find_client(wm.get_clients(), **matchers)
        if clients:
            wm.focus_and_raise(clients[0])
        else:
            if on_create:
                if not _create_spawn_hook.installed:
                    wm.on_create(_create_spawn_hook)
                    _create_spawn_hook.installed = True

                cw = wm.current_window
                if cw:
                    _create_spawn_queue.append((
                        time.time(), on_create, wm.current_window, matchers))

            spawn(cmd, switch_to_desktop)(wm)

    return inner

def focus_next(wm, c=None):
    c = c or wm.event_window
    clients = wm.find_client(wm.get_clients(), desktop=wm.get_window_desktop(c))
    idx = clients.index(c)
    newc = clients[(idx + 1) % len(clients)]
    wm.focus_and_raise(newc)

def focus_prev(wm, c=None):
    c = c or wm.event_window
    clients = wm.find_client(wm.get_clients(), desktop=wm.get_window_desktop(c))
    idx = clients.index(c)
    newc = clients[(idx - 1) % len(clients)]
    wm.focus_and_raise(newc)

