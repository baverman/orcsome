def spawn(cmd, switch_to_desktop=None):
    def inner(wm):
        import subprocess
        subprocess.Popen(cmd, shell=True)
        if switch_to_desktop is not None:
            wm.set_current_desktop(switch_to_desktop)

    return inner

def spawn_or_raise(cmd, switch_to_desktop=None, **matchers):
    def inner(wm):
        clients = wm.find_client(wm.get_clients(), **matchers)
        if clients:
            wm.focus_and_raise(clients[0])
        else:
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

