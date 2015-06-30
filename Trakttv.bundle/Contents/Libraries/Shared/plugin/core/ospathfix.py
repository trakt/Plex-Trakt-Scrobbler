import logging
import os
import sys

log = logging.getLogger(__name__)


def revert_fix(module, name):
    original = getattr(module, '_' + name, None)
    if not original:
        return

    setattr(module, name, original)

    log.debug('Reverted "%s.%s" method', module, name)


if sys.platform == 'win32':
    revert_fix(os, 'listdir')
    revert_fix(os, 'makedirs')

    revert_fix(os.path, 'exists')
