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
    try:
        execfile(rcfile, {'wm':wm})
    except:
        logger.getLogger(__name__).exception('Error on loading %s' % rcfile)
        sys.exit(1)

    wm.run()