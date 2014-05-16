import os
import re


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
