import os.path
import logging
import sys
import signal

from .core import WM

def run():
    config_dir = os.getenv('XDG_CONFIG_HOME', os.path.expanduser('~/.config'))
    rcfile = os.path.join(config_dir, 'orcsome', 'rc.py')

    logger = logging.getLogger('orcsome')
    logger.setLevel(logging.ERROR)
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("%(name)s %(levelname)s: %(message)s"))
    logger.addHandler(handler)

    wm = WM()

    import imp
    m = imp.new_module('orcsome.signals')
    m.on_key = wm.on_key
    m.on_create = wm.on_create
    m.on_property_change = wm.on_property_change
    m.on_destroy = wm.on_destroy

    sys.modules['orcsome.signals'] = m
    env = {}

    try:
        execfile(rcfile, env)
    except:
        logging.getLogger(__name__).exception('Error on loading %s' % rcfile)
        sys.exit(1)

    def term_handler(signum, frame):
        wm.dpy.close()
        print 'Closed'
        sys.exit(0)

    signal.signal(signal.SIGTERM, term_handler)

    wm.run()

def do():
    pass