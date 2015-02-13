import logging
import os

log = logging.getLogger(__name__)

EXCLUDE = [
    '__init__.py',
    'backup',
    'core'
]


def import_modules():
    current_dir = os.path.dirname(__file__)
    log.debug('current_dir: %r', current_dir)

    directory = os.path.abspath(os.path.join(current_dir, '..'))
    log.debug('directory: %r', directory)

    for name in os.listdir(directory):
        if name in EXCLUDE:
            continue

        if name.endswith('.pyc'):
            continue

        if name.endswith('.py'):
            name, _ = os.path.splitext(name)

        name = 'plugin.modules.%s' % name

        try:
            __import__(name)
        except Exception, ex:
            log.error('Unable to import module %r: %s', name, ex, exc_info=True)
