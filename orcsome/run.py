import os.path
import logging
import sys
import imp

from .core import WM

def _load_rcfile(wm, rcfile):
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

    sys.modules['orcsome.signals'].__dict__.clear()
    del sys.modules['orcsome.signals']


def _check_rcfile(rcfile):
    def on_key(key):
        assert isinstance(key, basestring), 'First argument to on_key must be string'

        def inner(func):
            return func

        return inner

    def on_create(*args, **matchers):
        assert matchers or args

        if args:
            assert len(args) == 1
            return args[0]

        if matchers:
            possible_args = set(('cls', 'role', 'name', 'desktop'))
            assert possible_args.union(matchers) == possible_args, \
                'Invalid matcher, must be one of %s' % possible_args

        def inner(func):
            return func

        return inner

    def on_property_change(*args):
        assert all(isinstance(r, basestring) for r in args)
        def inner(func):
            return inner

        return inner

    def on_destroy(window):
        raise Exception('Window? What?')

    m = imp.new_module('orcsome.signals')
    m.on_key = on_key
    m.on_create = on_create
    m.on_property_change = on_property_change
    m.on_destroy = on_destroy

    sys.modules['orcsome.signals'] = m
    env = {}

    try:
        execfile(rcfile, env)
    except:
        logging.getLogger(__name__).exception('Config file check failed %s' % rcfile)
        return False
    finally:
        sys.modules['orcsome.signals'].__dict__.clear()
        del sys.modules['orcsome.signals']

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