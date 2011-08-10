import os.path
import logging
import sys

from .core import WM, TestWM

def _load_rcfile(wm, rcfile):
    import orcsome
    orcsome._wm = wm

    env = {}
    try:
        execfile(rcfile, env)
    except:
        logging.getLogger(__name__).exception('Error on loading %s' % rcfile)
        sys.exit(1)


def _check_rcfile(rcfile):
    wm = TestWM()
    import orcsome
    orcsome._wm = wm

    env = {}

    try:
        execfile(rcfile, env)
    except:
        logging.getLogger(__name__).exception('Config file check failed %s' % rcfile)
        return False

    return True

def run():
    config_dir = os.getenv('XDG_CONFIG_HOME', os.path.expanduser('~/.config'))
    rcfile = os.path.join(config_dir, 'orcsome', 'rc.py')

    logger = logging.getLogger('orcsome')
    logger.setLevel(logging.ERROR)
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("%(name)s %(levelname)s: %(message)s"))
    logger.addHandler(handler)

    wm = WM()

    while True:
        _load_rcfile(wm, rcfile)
        wm.run()

        while True:
            if wm.handle_events():
                wm.dpy.close()
                sys.exit(0)
            else:
                if _check_rcfile(rcfile):
                    wm.clear_handlers()
                    print 'Restarting...'
                    break

def do():
    pass