import os.path
import logging
import sys

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

    sys.modules['orcsome.signals'] = m
    env = {}

    try:
        execfile(rcfile, env)
    except:
        logging.getLogger(__name__).exception('Error on loading %s' % rcfile)
        sys.exit(1)

    wm.run()

def do():
    pass