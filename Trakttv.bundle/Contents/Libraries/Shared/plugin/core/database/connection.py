from exception_wrappers.database.apsw.peewee import APSWDatabaseWrapper
from exception_wrappers.database.apsw.raw import APSWConnectionWrapper
from exception_wrappers.libraries import apsw
from exception_wrappers.libraries.playhouse.apsw_ext import APSWDatabase
import logging

BUSY_TIMEOUT = 3000

log = logging.getLogger(__name__)


def db_connect(path, type, name=None, wrapper=True):
    # Connect to new database
    if type == 'peewee':
        # Retrieve database class
        cls = APSWDatabaseWrapper if wrapper else APSWDatabase

        # Construct database
        db = cls(path, autorollback=True, journal_mode='WAL', timeout=BUSY_TIMEOUT)
    elif type == 'raw':
        # Retrieve connection class
        cls = APSWConnectionWrapper if wrapper else apsw.Connection

        # Construct connection
        db = cls(path, flags=apsw.SQLITE_OPEN_READWRITE | apsw.SQLITE_OPEN_CREATE | apsw.SQLITE_OPEN_WAL)
        db.setbusytimeout(BUSY_TIMEOUT)
    else:
        raise ValueError('Unknown database type: %r' % type)

    # Set database name
    if wrapper:
        db.name = name

    log.debug('Connected to database at %r', path)
    return db


def db_connection(database):
    if isinstance(database, APSWDatabase):
        return database.get_conn()

    if isinstance(database, apsw.Connection):
        return database

    raise ValueError('Unknown "database" parameter provided')
