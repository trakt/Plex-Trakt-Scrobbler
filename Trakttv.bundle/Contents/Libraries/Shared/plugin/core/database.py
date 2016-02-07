from plugin.core.environment import Environment

from datetime import datetime
from threading import RLock
from playhouse.apsw_ext import APSWDatabase
import apsw
import logging
import os

log = logging.getLogger(__name__)

BACKUP_PATH = os.path.join(Environment.path.plugin_data, 'Backups')
BUSY_TIMEOUT = 3000


class Database(object):
    _cache = {
        'peewee': {},
        'raw': {}
    }
    _lock = RLock()

    @classmethod
    def main(cls):
        return cls._get(Environment.path.plugin_database, 'peewee')

    @classmethod
    def cache(cls, name):
        return cls._get(os.path.join(Environment.path.plugin_caches, '%s.db' % name), 'raw')

    @classmethod
    def backup(cls, group, database, tag=None):
        timestamp = datetime.now()

        # Build backup directory/name
        directory, name = cls._backup_path(group, tag, timestamp)
        path = os.path.join(directory, name)

        log.info('[%s] Backing up database to %r', group, path)

        # Ensure directory exists
        if not os.path.exists(directory):
            os.makedirs(directory)

        # Backup database
        destination = cls._connect(path, 'raw')

        # Get `database` connection
        source = cls._connection(database)

        # Backup `source` database to `destination`
        try:
            cls._backup(group, source, destination)
        finally:
            # Close `destination` database
            destination.close()

        # Ensure path exists
        if not os.path.exists(path):
            log.error('Backup failed (file doesn\'t exist)')
            return False

        return True

    @classmethod
    def reset(cls, group, database, tag=None):
        # Backup database
        if not cls.backup(group, database, tag):
            return False

        log.info('[%s] Resetting database objects...', group)

        # Get `database` connection
        conn = cls._connection(database)

        # Drop all objects (index, table, trigger)
        conn.cursor().execute(
            "PRAGMA writable_schema = 1; "
            "DELETE FROM sqlite_master WHERE type IN ('table', 'index', 'trigger'); "
            "PRAGMA writable_schema = 0;"
        )

        # Recover space
        conn.cursor().execute('VACUUM;')

        # Check database integrity
        integrity, = conn.cursor().execute('PRAGMA INTEGRITY_CHECK;').fetchall()[0]

        if integrity != 'ok':
            log.error('[%s] Database integrity check error: %r', group, integrity)
            return False

        log.info('[%s] Database reset', group)
        return True

    @classmethod
    def _backup(cls, group, source, destination):
        with destination.backup('main', source, 'main') as b:
            while not b.done:
                # Backup page step
                b.step(100)

                # Report progress
                progress = float(b.pagecount - b.remaining) / b.pagecount

                log.debug('[%s] Backup Progress: %3d%%', group, progress * 100)

    @classmethod
    def _backup_path(cls, group, tag, timestamp):
        # Build directory
        directory = os.path.join(
            BACKUP_PATH,
            group,
            str(timestamp.year),
            '%02d' % timestamp.month
        )

        # Build filename
        name = '%02d_%02d%02d%02d%s.db' % (
            timestamp.day,
            timestamp.hour,
            timestamp.minute,
            timestamp.second,
            ('_%s' % tag) if tag else ''
        )

        return directory, name

    @classmethod
    def _connect(cls, path, type):
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

    @classmethod
    def _connection(cls, database):
        if isinstance(database, APSWDatabase):
            return database.get_conn()

        if isinstance(database, apsw.Connection):
            return database

        raise ValueError('Unknown "database" parameter provided')

    @classmethod
    def _get(cls, path, type):
        path = os.path.abspath(path)
        cache = cls._cache[type]

        with cls._lock:
            if path not in cache:
                cache[path] = cls._connect(path, type)

            # Return cached connection
            return cache[path]

