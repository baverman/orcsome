VERSION = '0.6'

_wm = None

def get_wm(immediate=False):
    if immediate:
        from .wm import ImmediateWM
        return ImmediateWM()
    else:
        return _wm
