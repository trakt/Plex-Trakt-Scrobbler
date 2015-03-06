import logging
import os

log = logging.getLogger(__name__)

shared_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))


def import_modules(directory, include=None, exclude=None):
    base_name = os.path.relpath(directory, shared_dir).replace(os.path.sep, '.')

    log.debug('Importing modules from: %s', base_name)

    for name in os.listdir(directory):
        if include and name not in include:
            continue

        if exclude and name in exclude:
            continue

        path = os.path.join(directory, name)

        if name.endswith('.pyc'):
            continue

        if os.path.isdir(path):
            # Ensure `__init__.py` exists in directory
            if not os.path.exists(os.path.join(path, '__init__.py')):
                continue
        elif name.endswith('.py'):
            name, _ = os.path.splitext(name)

        name = '.'.join([base_name, name])

        try:
            __import__(name)
        except Exception, ex:
            log.error('Unable to import module %r: %s', name, ex, exc_info=True)
