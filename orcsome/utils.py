import os
import re


class cached_property(object):
    def __init__(self, func):
        self.func = func
        self.__name__ = func.__name__
        self.__doc__ = func.__doc__

    def __get__(self, obj, cls):
        if obj is None:
            return self
        val = self.func(obj)
        obj.__dict__[self.__name__] = val
        return val


re_cache = {}
def match_string(pattern, data):
    if data is None:
        return False

    try:
        r = re_cache[pattern]
    except KeyError:
        r = re_cache[pattern] = re.compile(pattern)

    return r.match(data)


def spawn(cmd):
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


class Mixable(object):
    def mix(self, mixin):
        for name, value in mixin.__dict__.iteritems():
            if name == '__init__':
                value(self)
            elif name.startswith('__'):
                continue
            else:
                if name in self.__class__.__dict__:
                    raise Exception("Can't override base class method {}".format(name))
                setattr(self, name, value.__get__(self))


class ActionCaller(object):
    def __init__(self, obj, decorator):
        self.obj = obj
        self.decorator = decorator

    def __getattr__(self, name):
        func = getattr(self.obj, name)
        def result(*args, **kwargs):
            return self.decorator(lambda: func(*args, **kwargs))

        return result

    def __call__(self, func):
        return self.decorator(func)
