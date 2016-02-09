from playhouse.apsw_ext import APSWDatabase
from threading import RLock
import logging

log = logging.getLogger(__name__)


class DatabaseContext(object):
    def __init__(self, database):
        self.database = database

        self._previous = None

    def __enter__(self):
        # Wait for our turn to activate a database
        DATABASE_LOCK.acquire()

        # Store previous database
        self._previous = DATABASE_PROXY._database

        # Update current database
        DATABASE_PROXY._database = self.database

        log.info('Activated database: %r', self.database)

    def __exit__(self, exc_type, exc_val, exc_tb):
        # Restore previous database
        DATABASE_PROXY._database = self._previous

        log.info('Restored database: %r', self._previous)

        # Release lock
        DATABASE_LOCK.release()

    @classmethod
    def use(cls, database):
        return cls(database)


class DatabaseProxy(APSWDatabase):
    def __init__(self, database=None):
        self._database = database

    def __getattr__(self, key):
        if key == '_database':
            return self.__getattribute__(key)

        if self._database is None:
            raise EnvironmentError('No database available')

        return getattr(self._database, key)

    def __setattr__(self, key, value):
        if key == '_database':
            object.__setattr__(self, key, value)
            return

        if self._database is None:
            raise EnvironmentError('No database available')

        return setattr(self._database, key, value)


DATABASE_LOCK = RLock()
DATABASE_PROXY = DatabaseProxy()
