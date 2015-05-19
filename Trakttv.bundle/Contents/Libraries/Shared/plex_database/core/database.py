from playhouse.apsw_ext import APSWDatabase
import apsw
import logging
import os

log = logging.getLogger(__name__)

# Locate "com.plexapp.plugins.library.db"
db_path = os.path.abspath(os.environ['LIBRARY_DB'])

log.debug('Connecting to %r', db_path)

# Connect to database
db = APSWDatabase(db_path, flags=apsw.SQLITE_OPEN_READONLY, journal_mode='WAL')
