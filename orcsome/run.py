import sys
import signal
import os.path
import logging
import argparse

from . import VERSION, ev
from .wm import WM
from .actions import Actions
from .testwm import TestWM

logger = logging.getLogger(__name__)


def load_config(wm, config):
    import orcsome
    orcsome._wm = wm

    env = {}
    sys.path.insert(0, os.path.dirname(config))
    try:
        execfile(config, env)
    except:
        logger.exception('Error on loading %s' % config)
        sys.exit(1)
    finally:
        sys.path.pop(0)


def check_config(config):
    wm = TestWM()
    wm.mix(Actions)

    import orcsome
    orcsome._wm = wm

    env = {}
    sys.path.insert(0, os.path.dirname(config))
    try:
        execfile(config, env)
    except:
        logger.exception('Config file check failed %s' % config)
        return False
    finally:
        sys.path.pop(0)

    return True


def run():
    parser = argparse.ArgumentParser(version='%prog ' + VERSION)
    parser.add_argument('-l', '--log', dest='log', metavar='FILE',
        help='Path to log file (log to stdout by default)')

    config_dir = os.getenv('XDG_CONFIG_HOME', os.path.expanduser('~/.config'))
    default_rcfile = os.path.join(config_dir, 'orcsome', 'rc.py')
    parser.add_argument('-c', '--config', dest='config', metavar='FILE',
        default=default_rcfile, help='Path to config file (%(default)s)')

    args = parser.parse_args()

    if args.log:
        handler = logging.FileHandler(args.log)
    else:
        handler = logging.StreamHandler()

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    handler.setFormatter(logging.Formatter(
        "%(asctime)s %(name)s %(levelname)s: %(message)s"))
    root_logger.addHandler(handler)

    loop = ev.Loop()
    wm = WM(loop)
    wm.mix(Actions)

    def stop(l, w, e):
        wm.stop(True)
        loop.break_()

    sigint = ev.SignalWatcher(stop, signal.SIGINT)
    sigint.start(loop)

    def on_restart():
        if check_config(args.config):
            wm.stop()
            logger.info('Restarting...')
            load_config(wm, args.config)
            wm.init()

    wm.restart_handler = on_restart

    load_config(wm, args.config)
    wm.init()
    loop.run()
