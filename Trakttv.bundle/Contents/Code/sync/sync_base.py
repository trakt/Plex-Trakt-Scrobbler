from core.eventing import EventManager
from core.helpers import all, merge, get_filter, get_pref, total_seconds
from core.logger import Logger
from core.task import Task, CancelException
from plex.plex_library import PlexLibrary
from plex.plex_media_server import PlexMediaServer
from plex.plex_metadata import PlexMetadata
from plex.plex_objects import PlexEpisode

from datetime import datetime
from trakt import Trakt


log = Logger('sync.sync_base')


class Base(object):
    @classmethod
    def get_cache_id(cls):
        return EventManager.fire('sync.get_cache_id', single=True)


class PlexInterface(Base):
    @classmethod
    def sections(cls, types=None, keys=None, titles=None):
        # Default to 'titles' filter preference
        if titles is None:
            titles, _ = get_filter('filter_sections')

        return PlexMediaServer.get_sections(
            types, keys, titles,
            cache_id=cls.get_cache_id()
        )

    @classmethod
    def library(cls, types=None, keys=None, titles=None):
        # Default to 'titles' filter preference
        if titles is None:
            titles, _ = get_filter('filter_sections')

        return PlexLibrary.fetch(
            types, keys, titles,
            cache_id=cls.get_cache_id()
        )

    @classmethod
    def episodes(cls, key, parent=None):
        return PlexLibrary.fetch_episodes(key, parent, cache_id=cls.get_cache_id())

    @staticmethod
    def get_root(p_item):
        if isinstance(p_item, PlexEpisode):
            return p_item.parent

        return p_item

    @staticmethod
    def add_identifier(data, p_item):
        return PlexMetadata.add_identifier(data, p_item)

    @classmethod
    def to_trakt(cls, key, p_item, include_identifier=True):
        data = {}

        # Append episode attributes if this is a PlexEpisode
        if isinstance(p_item, PlexEpisode):
            k_season, k_episode = key

            data.update({
                'season': k_season,
                'episode': k_episode
            })

        if include_identifier:
            p_root = cls.get_root(p_item)

            data['title'] = p_root.title

            if p_root.year:
                data['year'] = p_root.year

            cls.add_identifier(data, p_root)

        return data


class TraktInterface(Base):
    merged_cache = {}

    @classmethod
    def merged(cls, media, watched=True, ratings=False, collected=False, extended='min'):
        cached = cls.merged_cache.get(media)

        # Check if the cached library is valid
        if cached and cached['cache_id'] == cls.get_cache_id():
            items, table = cached['result']

            log.debug(
                'merged() returned cached %s library with %s keys for %s items',
                media, len(table), len(items)
            )

            return items, table

        # Start building merged library
        start = datetime.utcnow()

        # Merge data
        items = {}

        # Merge watched library
        if watched and Trakt['user/library/%s' % media].watched(extended=extended, store=items) is None:
            log.warn('Unable to fetch watched library')
            return None, None

        # Merge ratings
        if ratings:
            if Trakt['user/ratings'].get(media, extended=extended, store=items) is None:
                log.warn('Unable to fetch ratings')
                return None, None

            # Fetch episode ratings (if we are fetching shows)
            if media == 'shows' and Trakt['user/ratings'].get('episodes', extended=extended, store=items) is None:
                log.warn('Unable to fetch episode ratings')
                return None, None

        # Merge collected library
        if collected and Trakt['user/library/%s' % media].collection(extended=extended, store=items) is None:
            log.warn('Unable to fetch collected library')
            return None, None

        # Generate item table with alternative keys
        table = items.copy()

        for key, item in table.items():
            # Skip first key (because it's the root_key)
            for alt_key in item.keys[1:]:
                table[alt_key] = item

        # Calculate elapsed time
        elapsed = datetime.utcnow() - start

        log.debug(
            'merged() built %s library with %s keys for %s items in %s seconds',
            media, len(table), len(items), total_seconds(elapsed)
        )

        # Cache for future calls
        cls.merged_cache[media] = {
            'cache_id': cls.get_cache_id(),
            'result': (items, table)
        }

        return items, table


class SyncBase(Base):
    key = None
    task = None
    title = "Unknown"
    children = []

    auto_run = True
    threaded = False

    plex = PlexInterface
    trakt = TraktInterface

    def __init__(self, manager, parent=None):
        self.manager = manager
        self.parent = parent

        # Activate children and create dictionary map
        self.children = dict([(x.key, x(manager, self)) for x in self.children])

        self.start_time = None
        self.artifacts = {}

    @classmethod
    def get_key(cls):
        if cls.task and cls.key and cls.task != cls.key:
            return '%s.%s' % (cls.task, cls.key)

        return cls.key or cls.task

    def reset(self, artifacts=None):
        self.start_time = datetime.utcnow()

        self.artifacts = artifacts.copy() if artifacts else {}

        for child in self.children.itervalues():
            child.reset(artifacts)

    def run(self, *args, **kwargs):
        self.reset(kwargs.get('artifacts'))

        # Trigger handlers and return if there was an error
        if not all(self.trigger(None, *args, **kwargs)):
            self.update_status(False)
            return False

        # Trigger children and return if there was an error
        if not all(self.trigger_children(*args, **kwargs)):
            self.update_status(False)
            return False

        self.update_status(True)
        return True

    def child(self, name):
        return self.children.get(name)

    def get_current(self):
        return self.manager.get_current()

    def is_stopping(self):
        task, _ = self.get_current()

        return task and task.stopping

    def check_stopping(self):
        if self.is_stopping():
            raise CancelException()

    @classmethod
    def get_enabled_functions(cls):
        result = []

        if cls.task in get_pref('sync_watched'):
            result.append('watched')

        if cls.task in get_pref('sync_ratings'):
            result.append('ratings')

        if cls.task in get_pref('sync_collection'):
            result.append('collected')

        return result

    #
    # Trigger
    #

    def trigger(self, funcs=None, *args, **kwargs):
        single = kwargs.pop('single', False)

        if funcs is None:
            funcs = [x[4:] for x in dir(self) if x.startswith('run_')]
        elif type(funcs) is not list:
            funcs = [funcs]

        # Get references to functions
        funcs = [(name, getattr(self, 'run_' + name)) for name in funcs if hasattr(self, 'run_' + name)]

        return self.trigger_run(funcs, single, *args, **kwargs)

    def trigger_children(self, *args, **kwargs):
        single = kwargs.pop('single', False)

        children = [
            (child.key, child.run) for (_, child) in self.children.items()
            if child.auto_run
        ]


        return self.trigger_run(children, single, *args, **kwargs)

    def trigger_run(self, funcs, single, *args, **kwargs):
        if not funcs:
            return []

        if self.threaded:
            tasks = []

            for name, func in funcs:
                task = Task(func, *args, **kwargs)
                tasks.append(task)

                task.spawn('sync.%s.%s' % (self.key, name))

            # Wait until everything is complete
            results = []

            for task in tasks:
                task.wait()
                results.append(task.result)

            return results

        # Run each task and collect results
        results = [func(*args, **kwargs) for (_, func) in funcs]

        if not single:
            return results

        return results[0]

    #
    # Status / Progress
    #

    def start(self, end, start=0):
        EventManager.fire(
            'sync.%s.started' % self.get_key(),
            start=start, end=end
        )

    def progress(self, value):
        EventManager.fire(
            'sync.%s.progress' % self.get_key(),
            value=value
        )

    def finish(self):
        EventManager.fire(
            'sync.%s.finished' % self.get_key()
        )

    def update_status(self, success, end_time=None, start_time=None, section=None):
        if end_time is None:
            end_time = datetime.utcnow()

        # Update task status
        status = self.get_status(section)
        status.update(success, start_time or self.start_time, end_time)

        log.info(
            'Task "%s" finished - success: %s, start: %s, elapsed: %s',
            status.key,
            status.previous_success,
            status.previous_timestamp,
            status.previous_elapsed
        )

    def get_status(self, section=None):
        """Retrieve the status of the current syncing task.

        :rtype : SyncStatus
        """
        if section is None:
            # Determine section from current state
            task, _ = self.get_current()
            if task is None:
                return None

            section = task.kwargs.get('section')

        return self.manager.get_status(self.task or self.key, section)

    #
    # Artifacts
    #

    def retrieve(self, key, single=False):
        if single:
            return self.artifacts.get(key)

        return self.artifacts.get(key, [])

    def store(self, key, data, single=False):
        if single:
            self.artifacts[key] = data
            return

        if key not in self.artifacts:
            self.artifacts[key] = []

        self.artifacts[key].append(data)

    def store_episodes(self, key, show, episodes=None, artifact=None):
        if episodes is None:
            episodes = self.child('episode').artifacts.get(artifact or key)

        if episodes is None:
            return

        self.store(key, merge({'episodes': episodes}, show))

    # TODO switch to a streamed format (to avoid the MemoryError)
    def save(self, group, data, source=None):
        name = '%s.%s' % (group, self.key)

        if source:
            name += '.%s' % source

        try:
            log.debug('Saving artifacts to "%s.json"', name)
            Data.Save(name + '.json', repr(data))
        except MemoryError:
            log.warn('Unable to save artifacts, out of memory')
