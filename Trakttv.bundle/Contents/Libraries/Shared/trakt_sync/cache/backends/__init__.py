import logging

log = logging.getLogger(__name__)


def import_backend(module, name):
    try:
        m = __import__(module, fromlist=[name])

        return getattr(m, name, None)
    except ImportError, ex:
        log.warn('Unable to import %r - %s', name, ex, exc_info=True)
        return None


StashBackend = import_backend('trakt_sync.cache.backends.stash_', 'StashBackend')


__all__ = [
    'StashBackend'
]
