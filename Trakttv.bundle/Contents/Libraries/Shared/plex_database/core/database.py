import logging
import os

log = logging.getLogger(__name__)

# Try import "apsw"
try:
    import apsw
except ImportError as ex:
    log.error('Unable to import "apsw": %s', ex, exc_info=True)
    apsw = None

# Try import "playhouse.apsw_ext"
try:
    from playhouse.apsw_ext import APSWDatabase
except ImportError as ex:
    log.error('Unable to import "playhouse.apsw_ext": %s', ex, exc_info=True)
    APSWDatabase = None

# Locate "com.plexapp.plugins.library.db"
if os.environ.get('LIBRARY_DB'):
    db_path = os.path.abspath(os.environ['LIBRARY_DB'])
else:
    log.warn('Unable to locate plex database')
    db_path = None

# Connect to database
if db_path and apsw and APSWDatabase:
    log.debug('Connecting to %r', db_path)

    db = APSWDatabase(db_path, flags=apsw.SQLITE_OPEN_READONLY, journal_mode='WAL')
else:
    db = None
