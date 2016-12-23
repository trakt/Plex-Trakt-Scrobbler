from plugin.core.database.manager import DatabaseManager

from stash import Stash, ApswArchive
from threading import Lock, Thread
import logging
import time

DEFAULT_SERIALIZER = 'msgpack:///'

log = logging.getLogger(__name__)


class CacheManager(object):
    active = {}

    _lock = Lock()

    _process_interval = 10
    _process_running = True
    _process_thread = None

    @classmethod
    def get(cls, key, serializer=DEFAULT_SERIALIZER):
        with cls._lock:
            if key in cls.active:
                return cls.active[key]

            return cls.open(
                key,
                serializer=serializer,
                block=False
            )

    @classmethod
    def open(cls, key, serializer=DEFAULT_SERIALIZER, block=True):
        if block:
            # Open cache in lock
            with cls._lock:
                return cls.open(
                    key,
                    serializer=serializer,
                    block=False
                )

        # Construct cache
        cls.active[key] = Cache(
            key,
            serializer=serializer
        )

        # Ensure process thread has started
        cls._start()

        # Return cache
        log.debug('Opened "%s" cache (serializer: %r)', key, serializer)
        return cls.active[key]

    @classmethod
    def _start(cls):
        if cls._process_thread is not None:
            return

        cls._process_thread = Thread(name='CacheManager._process', target=cls._process)
        cls._process_thread.daemon = True

        cls._process_thread.start()

    @classmethod
    def _process(cls):
        try:
            cls._process_run()
        except Exception as ex:
            log.error('Exception raised in CacheManager: %s', ex, exc_info=True)

    @classmethod
    def _process_run(cls):
        while cls._process_running:
            # Retrieve current time
            now = time.time()

            # Retrieve active caches
            with cls._lock:
                caches = cls.active.values()

            # Sync caches that have been queued
            for cache in caches:
                if cache.flush_at is None or cache.flush_at > now:
                    continue

                cache.flush()

            time.sleep(cls._process_interval)


class Cache(object):
    def __init__(self, key, serializer=DEFAULT_SERIALIZER):
        self.key = key

        self.stash = self._construct(key, serializer=serializer)

        self._flush_at = None
        self._flush_lock = Lock()

    @property
    def flush_at(self):
        return self._flush_at

    @staticmethod
    def _construct(key, serializer=DEFAULT_SERIALIZER):
        # Parse `key`
        fragments = key.split('.')

        if len(fragments) != 2:
            raise ValueError('Invalid "key" format')

        database, table = tuple(fragments)

        # Construct cache
        return Stash(
            ApswArchive(DatabaseManager.cache(database), table),
            'lru:///?capacity=500&compact_threshold=1500',
            serializer=serializer,
            key_transform=(lambda k: str(k), lambda k: k)
        )

    def get(self, key, default=None):
        return self.stash.get(key, default)

    def prime(self, keys=None, force=False):
        return self.stash.prime(keys, force)

    def __getitem__(self, key):
        return self.stash[key]

    def __setitem__(self, key, value):
        self.stash[key] = value

    def flush(self, force=False):
        with self._flush_lock:
            self._flush(force=force)

    def _flush(self, force=False):
        if not force and self._flush_at is None:
            return

        try:
            self.stash.flush()

            log.debug('Flushed "%s" cache', self.key)
        except Exception as ex:
            log.error('Unable to flush "%s" cache: %s', self.key, ex, exc_info=True)
        finally:
            self.flush_clear()

    def flush_queue(self, delay=120):
        log.debug('Queued flush for "%s" cache in %ss', self.key, delay)

        self._flush_at = time.time() + 120

    def flush_clear(self):
        if self._flush_at is None:
            return

        log.debug('Cleared flush for "%s" cache', self.key)

        self._flush_at = None
