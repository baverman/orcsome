from array import array
from ._xlib import ffi, lib

NULL = ffi.NULL
globals().update(lib.__dict__)

NONE = 0L


class AtomCache(object):
    def __init__(self, dpy):
        self.dpy = dpy
        self._cache = {}

    def __getitem__(self, name):
        try:
            return self._cache[name]
        except KeyError:
            pass

        atom = self._cache[name] = XInternAtom(self.dpy, name, False)
        return atom


ITEM_SIZE = array('L').itemsize

def get_window_property(display, window, property, type=0, split=False, size=50):
    type_return = ffi.new('Atom *')
    fmt_return = ffi.new('int *')
    nitems_return = ffi.new('unsigned long *')
    bytes_after = ffi.new('unsigned long *')
    data = ffi.new('unsigned char **')
    XGetWindowProperty(display, window, property, 0, size, False, type,
        type_return, fmt_return, nitems_return, bytes_after, data)

    fmt = fmt_return[0]
    bafter = bytes_after[0]
    result = b''
    if fmt == 32:
        result += str(ffi.buffer(data[0], nitems_return[0]*ITEM_SIZE))
    elif fmt == 8:
        result += str(ffi.buffer(data[0], nitems_return[0]))
    elif not fmt:
        return None
    else:
        raise Exception('Unknown format {}'.format(fmt))

    if bafter:
        XFree(data[0])
        XGetWindowProperty(display, window, property, size, bafter / 4 + 1,
            False, type, type_return, fmt_return, nitems_return, bytes_after, data)
        fmt = fmt_return[0]
        if fmt == 32:
            result += str(ffi.buffer(data[0], nitems_return[0]*ITEM_SIZE))
        elif fmt == 8:
            result += str(ffi.buffer(data[0], nitems_return[0]))
        else:
            raise Exception('Unknown format {}'.format(fmt))

    if fmt_return[0] == 32:
        result = array('L', result)
    elif fmt_return[0] == 8:
        result = result.rstrip(b'\x00')
        if split:
            result = result.split(b'\x00')
    else:
        raise Exception('Unknown format {}'.format(fmt_return[0]))

    XFree(data[0])
    return result


def set_window_property(display, window, property, type, fmt, values):
    if fmt == 32:
        if values:
            data = ffi.cast('unsigned char *', ffi.new('XID[]', values))
        else:
            data = ''
    elif fmt == 8:
        data = values
    else:
        raise Exception('Unknown format {}'.format(fmt))

    XChangeProperty(display, window, property, type, fmt, PropModeReplace,
        data, len(values))


def get_kbd_group(display):
    state = ffi.new('XkbStateRec *')
    XkbGetState(display, XkbUseCoreKbd, state)
    return state[0].group


def set_kbd_group(display, group):
    XkbLockGroup(display, XkbUseCoreKbd, group)
    XFlush(display)
