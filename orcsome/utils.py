import threading
import os
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
