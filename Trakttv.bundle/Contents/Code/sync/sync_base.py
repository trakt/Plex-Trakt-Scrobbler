from core.eventing import EventManager
from core.logger import Logger
from core.trakt import Trakt
from plex.media_server_new import PlexMediaServer


log = Logger('sync.sync_base')


class Base(object):
    @classmethod
    def get_cache_id(cls):
        return EventManager.fire('sync.get_cache_id', single=True)


class PlexInterface(Base):
    @classmethod
    def sections(cls, types=None, keys=None):
        return PlexMediaServer.get_sections(types, keys, cache_id=cls.get_cache_id())

    @classmethod
    def library(cls, types=None, keys=None):
        return PlexMediaServer.get_library(types, keys, cache_id=cls.get_cache_id())

    @classmethod
    def episodes(cls, key):
        return PlexMediaServer.get_episodes(key, cache_id=cls.get_cache_id())


class TraktInterface(Base):
    # TODO per-sync cached results
    @classmethod
    def library(cls, media, marked, extended='min'):
        return Trakt.User.get_library(media, marked, extended).get('data')

    # TODO per-sync cached results
    @classmethod
    def ratings(cls, media):
        return Trakt.User.get_ratings(media)


class SyncBase(Base):
    title = "Unknown"
    children = []

    plex = PlexInterface
    trakt = TraktInterface

    def __init__(self):
        # Activate children and create dictionary map
        self.children = [x() for x in self.children]

    def run(self):
        # Run sub functions (starting with 'run_')
        sub_functions = [(x, getattr(self, x)) for x in dir(self) if x.startswith('run_')]

        for name, func in sub_functions:
            log.debug('Running sub-function in task %s with name "%s"' % (self, name))
            func()

        # Run child tasks
        for child in self.children:
            log.debug('Running child task %s' % child)
            child.run()

    @staticmethod
    def update_progress(current, start=0, end=100):
        raise ReferenceError()

    @staticmethod
    def is_stopping():
        raise ReferenceError()
