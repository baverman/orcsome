import os
import re
import threading

from select import select

class Timer(threading.Thread):
    def __init__(self, interval, target, *args, **kwargs):
        threading.Thread.__init__(self)
        self.interval = interval
        self.target = target
        self.args = args
        self.kwargs = kwargs

        self.rfd = self.wfd = None
        self.cancel_requested = False

    def run(self):
        self.rfd, self.wfd = os.pipe()
        while True:
            readable, _, exc = select([self.rfd], [], [], self.interval)

            if self.cancel_requested:
                break

            self.target(*self.args, **self.kwargs)

    def cancel(self, block=True):
        self.cancel_requested = True
        os.write(self.wfd, '1')
        if block:
            self.join()

        os.close(self.rfd)
        os.close(self.wfd)


def lazy_attr(self, name):
    value = object.__getattribute__(self, '_' + name)()
    setattr(self, name, value)
    return value


re_cache = {}
def match_string(pattern, data):
    if data is None:
        return False

    try:
        r = re_cache[pattern]
    except KeyError:
        r = re_cache[pattern] = re.compile(pattern)

    return r.match(data)
