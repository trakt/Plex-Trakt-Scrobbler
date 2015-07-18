from plugin.core.environment import Environment

from threading import RLock
from playhouse.apsw_ext import APSWDatabase
import apsw
import logging
import os

log = logging.getLogger(__name__)

BUSY_TIMEOUT = 3000


class Database(object):
    _cache = {
        'peewee': {},
        'raw': {}
    }
    _lock = RLock()

    @classmethod
    def main(cls):
        return cls._connect(Environment.path.plugin_database, 'peewee')

    @classmethod
    def cache(cls, name):
        return cls._connect(os.path.join(Environment.path.plugin_caches, '%s.db' % name), 'raw')

    @classmethod
    def _connect(cls, path, type):
        path = os.path.abspath(path)
        cache = cls._cache[type]

        with cls._lock:
            if path not in cache:
                # Connect to new database
                if type == 'peewee':
                    cache[path] = APSWDatabase(path, autorollback=True, journal_mode='WAL', timeout=BUSY_TIMEOUT)
                elif type == 'raw':
                    cache[path] = apsw.Connection(path, flags=apsw.SQLITE_OPEN_READWRITE | apsw.SQLITE_OPEN_CREATE | apsw.SQLITE_OPEN_WAL)
                    cache[path].setbusytimeout(BUSY_TIMEOUT)

                log.debug('Connected to database at %r', path)

            # Return cached connection
            return cache[path]
