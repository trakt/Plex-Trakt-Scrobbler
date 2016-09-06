__version__ = '0.8.0'

import logging
log = logging.getLogger(__name__)

try:
    from plex_database.library import Library
    from plex_database.matcher import Matcher
except ImportError, ex:
    log.warn('Unable to import "plex_database" - %s', ex, exc_info=True)
