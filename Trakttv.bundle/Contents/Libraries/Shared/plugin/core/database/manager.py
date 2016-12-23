from plugin.core.backup import BackupManager
from plugin.core.database.connection import db_connect, db_connection
from plugin.core.environment import Environment

from exception_wrappers import DisabledError
from threading import RLock
import logging
import os

log = logging.getLogger(__name__)


class DatabaseManager(object):
    _cache = {
        'peewee': {},
        'raw': {}
    }
    _lock = RLock()

    @classmethod
    def main(cls):
        return cls._get(Environment.path.plugin_database, 'peewee', name='plugin database')

    @classmethod
    def cache(cls, name):
        return cls._get(os.path.join(Environment.path.plugin_caches, '%s.db' % name), 'raw', name='%s cache' % name)

    @classmethod
    def reset(cls, group, database, tag=None):
        # Backup database
        if not BackupManager.database.backup(group, database, tag):
            return False

        log.info('[%s] Resetting database objects...', group)

        # Get `database` connection
        conn = db_connection(database)

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
    def _get(cls, path, type, **kwargs):
        path = os.path.abspath(path)
        cache = cls._cache[type]

        with cls._lock:
            if path not in cache:
                try:
                    cache[path] = db_connect(path, type, **kwargs)
                except DisabledError:
                    cache[path] = None

            # Return cached connection
            return cache[path]
