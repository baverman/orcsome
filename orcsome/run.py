import os.path
import logging
import sys

from .core import WM, TestWM

def _load_rcfile(wm, rcfile):
    import orcsome
    orcsome._wm = wm

    env = {}
    sys.path.insert(0, os.path.dirname(rcfile))
    try:
        execfile(rcfile, env)
    except:
        logging.getLogger(__name__).exception('Error on loading %s' % rcfile)
        sys.exit(1)
    finally:
        sys.path.pop(0)


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

    def shutdown():
        wm.stop(True)
        wm.dpy.close()
        sys.exit(0)

    while True:
        _load_rcfile(wm, rcfile)
        wm.run()

        while True:
            if wm.handle_events():
                shutdown()
            else:
                if _check_rcfile(rcfile):
                    wm.stop()
                    print 'Restarting...'
                    break

def do():
    pass