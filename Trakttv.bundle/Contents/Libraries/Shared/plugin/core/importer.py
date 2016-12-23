import logging
import os

log = logging.getLogger(__name__)

shared_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))


def import_modules(directory, include=None, exclude=None):
    base_name = os.path.relpath(directory, shared_dir).replace(os.path.sep, '.')

    log.debug('Importing modules from: %s', base_name)

    for name in os.listdir(directory):
        # Match `name` against filters
        if include and name not in include:
            continue

        if exclude and name in exclude:
            continue

        # Build module path
        path = os.path.join(directory, name)

        # Check if `path` has a valid module
        if not is_module(path, name):
            continue

        # Import module
        if not import_module(path, base_name, name):
            log.warn('Unable to import module: %r', name)


def import_module(path, base_name, name):
    # Get full module name
    full_name = get_name(path, base_name, name)

    if full_name is None:
        return False

    # Try import module
    try:
        __import__(full_name)
        return True
    except Exception as ex:
        log.error('Exception raised trying to import module %r: %s', full_name, ex, exc_info=True)

    return False


def get_name(path, base_name, name):
    # Strip extension from module files
    if os.path.isfile(path):
        name, _ = os.path.splitext(name)

    # Return file module name
    return '%s.%s' % (
        base_name,
        name
    )


def is_module(path, name):
    # Check module file is valid
    if os.path.isfile(path):
        return is_module_file(path, name)

    # Check module directory is valid
    if os.path.isdir(path):
        return is_module_directory(path, name)

    return False


def is_module_directory(path, name):
    # Ignore directories without an "__init__.py" file
    if not os.path.exists(os.path.join(path, '__init__.py')):
        return False

    # Ignore directories with a "." or "_" prefix
    if name.startswith('.') or name.startswith('_'):
        log.info('Ignoring invalid module: %r', path)
        return False

    # Ignore directories with a "." suffix
    if name.endswith('.'):
        log.info('Ignoring invalid module: %r', path)
        return False

    return True


def is_module_file(path, name):
    # Ignore files without the "*.py" extension
    if not name.endswith('.py'):
        return False

    # Split extension from `name`
    name, _ = os.path.splitext(name)

    # Ignore files with a "." or "_" prefix
    if name.startswith('.') or name.startswith('_'):
        log.info('Ignoring invalid module: %r', path)
        return False

    # Ignore files with a "." suffix
    if name.endswith('.'):
        log.info('Ignoring invalid module: %r', path)
        return False

    # Valid module
    return True
