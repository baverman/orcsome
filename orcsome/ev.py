from time import time
from ._ev import ffi, lib

NULL = ffi.NULL
globals().update(lib.__dict__)


class Loop(object):
    def __init__(self):
        self._loop = ev_loop_new(EVBACKEND_SELECT)

    def destroy(self):
        ev_loop_destroy(self._loop)

    def run(self, flags=0):
        ev_run(self._loop, flags)

    def break_(self, flags=EVBREAK_ALL):
        ev_break(self._loop, flags)


class IOWatcher(object):
    def __init__(self, cb, fd, flags):
        self._watcher = ffi.new('ev_io*')
        self._cb = ffi.callback('io_cb', cb)
        ev_io_init(self._watcher, self._cb, fd, flags)

    def start(self, loop):
        ev_io_start(loop._loop, self._watcher)

    def stop(self, loop):
        ev_io_stop(loop._loop, self._watcher)


class SignalWatcher(object):
    def __init__(self, cb, signal):
        self._watcher = ffi.new('ev_signal*')
        self._cb = ffi.callback('signal_cb', cb)
        ev_signal_init(self._watcher, self._cb, signal)

    def start(self, loop):
        ev_signal_start(loop._loop, self._watcher)

    def stop(self, loop):
        ev_signal_stop(loop._loop, self._watcher)


class TimerWatcher(object):
    def __init__(self, cb, after, repeat=0.0):
        self._after = after
        self._repeat = repeat
        self._watcher = ffi.new('ev_timer*')
        self._cb = ffi.callback('timer_cb', cb)
        ev_timer_init(self._watcher, self._cb, after, repeat)

    def start(self, loop, after=None, repeat=None):
        if after or repeat:
            self._after = after or self._after
            self._repeat = repeat or self._repeat
            ev_timer_set(self._watcher, self._after, self._repeat)

        self.next_stop = time() + self._after
        ev_timer_start(loop._loop, self._watcher)

    def stop(self, loop):
        ev_timer_stop(loop._loop, self._watcher)

    def again(self, loop):
        self.next_stop = time() + self._repeat
        ev_timer_again(loop._loop, self._watcher)

    def remaining(self, loop):
        return ev_timer_remaining(loop._loop, self._watcher)

    def update_next_stop(self):
        self.next_stop = time() + self._repeat

    def overdue(self, timeout):
        return time() > self.next_stop + timeout
