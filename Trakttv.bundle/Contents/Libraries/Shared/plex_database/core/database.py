from playhouse.apsw_ext import APSWDatabase
import apsw
import logging
import os

log = logging.getLogger(__name__)

# Locate "com.plexapp.plugins.library.db"
if os.environ.get('LIBRARY_DB'):
    db_path = os.path.abspath(os.environ['LIBRARY_DB'])
else:
    log.warn('Unable to locate plex database')
    db_path = None

# Connect to database
if db_path:
    log.debug('Connecting to %r', db_path)

    db = APSWDatabase(db_path, flags=apsw.SQLITE_OPEN_READONLY, journal_mode='WAL')
else:
    db = None
