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
    def merged(cls, media, marked, include_ratings=False, extended='min'):
        return Trakt.User.get_merged(media, marked, include_ratings, extended)

    # TODO per-sync cached results
    @classmethod
    def library(cls, media, marked, extended='min'):
        return Trakt.User.get_library(media, marked, extended).get('data')

    # TODO per-sync cached results
    @classmethod
    def ratings(cls, media):
        return Trakt.User.get_ratings(media)


class SyncBase(Base):
    key = None
    title = "Unknown"
    children = []

    auto_run = True

    plex = PlexInterface
    trakt = TraktInterface

    def __init__(self):
        # Activate children and create dictionary map
        self.children = dict([(x.key, x()) for x in self.children])

    def run(self, *args, **kwargs):
        self.trigger(None, *args, **kwargs)
        self.trigger_children(*args, **kwargs)

    def child(self, name):
        return self.children.get(name)

    def trigger(self, funcs=None, *args, **kwargs):
        single = kwargs.pop('single', False)
        ignore_missing = kwargs.pop('ignore_missing', False)

        results = []

        if funcs is None:
            funcs = [x[4:] for x in dir(self) if x.startswith('run_')]
        elif type(funcs) is not list:
            funcs = [funcs]

        for name in funcs:
            func = getattr(self, 'run_' + name, None)

            if func is None:
                if ignore_missing:
                    continue

                raise ValueError('Unable to find sub-function with the name "%s"' % name)

            #log.debug('Running sub-function in task %s with name "%s"' % (self, name))
            results.append(func(*args, **kwargs))

        if single:
            return results[0]

        return results

    def trigger_children(self, *args, **kwargs):
        for key, child in self.children.items():
            if not child.auto_run:
                continue

            log.debug('Running child task %s' % child)
            child.run(*args, **kwargs)

    @staticmethod
    def update_progress(current, start=0, end=100):
        raise ReferenceError()

    @staticmethod
    def is_stopping():
        raise ReferenceError()

    @staticmethod
    def get_enabled_functions():
        result = []

        if Prefs['sync_watched']:
            result.append('watched')

        if Prefs['sync_ratings']:
            result.append('ratings')

        return result
