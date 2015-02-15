from threading import Thread
import logging
import os

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
        'methods'
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

        except Exception, ex:
            log.error('Unable to start %r module: %s', kls, ex, exc_info=True)

    log.debug('Finished starting %d module(s)', len(modules))


def spawn(func, *args, **kwargs):
    name = kwargs.pop('_name', func.__name__)

    def wrapper(thread_name, args, kwargs):
        try:
            func(*args, **kwargs)
        except Exception, ex:
            log.error('Thread "%s" raised an exception: %s', thread_name, ex, exc_info=True)

    thread = Thread(target=wrapper, name=name, args=args, kwargs=kwargs)
    thread.start()

    log.debug("Spawned thread with name '%s'" % name)
    return thread
