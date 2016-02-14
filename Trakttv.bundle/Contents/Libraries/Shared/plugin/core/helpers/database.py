from playhouse.apsw_ext import APSWDatabase
import apsw
import logging

BUSY_TIMEOUT = 3000

log = logging.getLogger(__name__)


def db_connect(path, type):
    # Connect to new database
    if type == 'peewee':
        db = APSWDatabase(path, autorollback=True, journal_mode='WAL', timeout=BUSY_TIMEOUT)
    elif type == 'raw':
        db = apsw.Connection(path, flags=apsw.SQLITE_OPEN_READWRITE | apsw.SQLITE_OPEN_CREATE | apsw.SQLITE_OPEN_WAL)
        db.setbusytimeout(BUSY_TIMEOUT)
    else:
        raise ValueError('Unknown database type: %r' % type)

    log.debug('Connected to database at %r', path)
    return db


def db_connection(database):
    if isinstance(database, APSWDatabase):
        return database.get_conn()

    if isinstance(database, apsw.Connection):
        return database

    raise ValueError('Unknown "database" parameter provided')
