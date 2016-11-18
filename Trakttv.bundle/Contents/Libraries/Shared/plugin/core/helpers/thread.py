from threading import Thread
import logging
import os

from plugin.core.helpers.variable import resolve
from plugin.core.importer import import_modules

log = logging.getLogger(__name__)


MODULES = {}


def module(start=False, priority=100, blocking=False):
    def wrap(kls):
        module_register(kls, start=start, priority=priority, blocking=blocking)
        return kls

    return wrap


def module_register(kls, **kwargs):
    start = kwargs.get('start', False)

    if start:
        # Validate "start" option
        f_start = getattr(kls, 'start', None)

        if not f_start or not f_start.im_self:
            log.warn('Unable to find bound "start" method for %r', kls)
            start = False

    # Register module
    MODULES[kls] = {
        'start': start,

        'priority': kwargs.get('priority', 100),
        'blocking': kwargs.get('blocking', False)
    }


def module_start():
    # Import modules
    plugin_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
    log.debug('plugin_dir: %r', plugin_dir)

    import_modules(os.path.join(plugin_dir, 'api'), exclude=[
        '__init__.py',
        'core'
    ])

    import_modules(os.path.join(plugin_dir, 'api', 'account'), exclude=[
        '__init__.py'
    ])

    import_modules(os.path.join(plugin_dir, 'api', 'session'), exclude=[
        '__init__.py'
    ])

    import_modules(os.path.join(plugin_dir, 'managers'), exclude=[
        '__init__.py',
        'core'
    ])

    import_modules(os.path.join(plugin_dir, 'modules'), exclude=[
        '__init__.py',
        'backup',
        'core'
    ])

    import_modules(os.path.join(plugin_dir, 'scrobbler'), exclude=[
        '__init__.py',
        'core',
        'handlers',
        'methods'
    ])

    import_modules(os.path.join(plugin_dir, 'scrobbler', 'handlers'), exclude=[
        '__init__.py'
    ])

    # Start modules
    modules = sorted(MODULES.items(), key=lambda item: item[1]['priority'])

    log.debug('Starting %d module(s)...', len(modules))

    for kls, options in modules:
        if not options['start']:
            continue

        log.debug(' -> %s (priority: %d, blocking: %s)', kls.__name__, options['priority'], options['blocking'])

        f_start = getattr(kls, 'start')

        try:
            # Start module
            if options['blocking']:
                f_start()
            else:
                options['thread'] = spawn(f_start, _name=kls.__name__)

        except Exception as ex:
            log.error('Unable to start %r module: %s', kls, ex, exc_info=True)

    log.debug('Finished starting %d module(s)', len(modules))


def spawn(func, *args, **kwargs):
    name = kwargs.pop('_name', func.__name__)

    # Construct thread wrapper to log exceptions
    def wrapper(th_name, *args, **kwargs):
        try:
            func(*args, **kwargs)
        except Exception as ex:
            log.error('Thread "%s" raised an exception: %s', th_name, ex, exc_info=True)

    # Spawn thread
    try:
        thread = Thread(target=wrapper, name=name, args=[name] + (args or []), kwargs=kwargs)
        thread.start()
    except Exception as ex:
        log.warn('Unable to spawn thread: %s', ex, exc_info=True)
        return None

    log.info('Spawned thread with name "%s"', name)
    return thread


def synchronized(lock):
    def outer(func):
        def inner(*args, **kwargs):
            with resolve(lock, args[0]):
                return func(*args, **kwargs)

        return inner

    return outer
