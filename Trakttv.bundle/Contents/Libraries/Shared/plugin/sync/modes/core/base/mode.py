from plugin.core.filters import Filters
from plugin.sync.core.enums import SyncData, SyncMedia, SyncMode
from plugin.sync.core.guid import GuidMatch

from plex import Plex
import elapsed
import itertools
import logging

log = logging.getLogger(__name__)

TRAKT_DATA_MAP = {
    SyncMedia.Movies: [
        SyncData.Collection,
        SyncData.Playback,
        SyncData.Ratings,
        SyncData.Watched,
        # SyncData.Watchlist
    ],
    SyncMedia.Shows: [
        SyncData.Ratings
    ],
    SyncMedia.Seasons: [
        SyncData.Ratings
    ],
    SyncMedia.Episodes: [
        SyncData.Collection,
        SyncData.Playback,
        SyncData.Ratings,
        SyncData.Watched,
        # SyncData.Watchlist
    ]
}

DATA_PREFERENCE_MAP = {
    SyncData.Collection:    'sync.collection.mode',
    SyncData.Playback:      'sync.playback.mode',
    SyncData.Ratings:       'sync.ratings.mode',
    SyncData.Watched:       'sync.watched.mode',

    # Lists
    SyncData.Liked:         'sync.lists.liked.mode',
    SyncData.Personal:      'sync.lists.personal.mode',
    SyncData.Watchlist:     'sync.lists.watchlist.mode',
}


class Mode(object):
    data = None
    mode = None

    children = []

    def __init__(self, task):
        self.__task = task

        self.children = [c(task) for c in self.children]

        # Retrieve enabled data
        self.enabled_data = self.get_enabled_data()

        # Determine if mode should be enabled
        self.enabled = len(self.enabled_data) > 0

        if not self.enabled:
            log.debug('Mode %r disabled on: %r', self.mode, self)

    @property
    def current(self):
        return self.__task

    @property
    def configuration(self):
        return self.__task.configuration

    @property
    def handlers(self):
        return self.__task.handlers

    @property
    def modes(self):
        return self.__task.modes

    @property
    def plex(self):
        if not self.current or not self.current.state:
            return None

        return self.current.state.plex

    @property
    def trakt(self):
        if not self.current or not self.current.state:
            return None

        return self.current.state.trakt

    def construct(self):
        pass

    def start(self):
        pass

    def run(self):
        raise NotImplementedError

    def finish(self):
        pass

    def stop(self):
        pass

    def checkpoint(self):
        if self.current is None:
            return

        self.current.checkpoint()

    def execute_children(self, name, force=None):
        # Run method on children
        for c in self.children:
            if not force and not c.enabled:
                log.debug('Ignoring %s() call on child: %r', name, c)
                continue

            # Find method `name` in child
            log.info('Executing %s() on child: %r', name, c)

            func = getattr(c, name, None)

            if not func:
                log.warn('Unknown method: %r', name)
                continue

            # Run method on child
            func()

    def execute_episode_action(self, mode, data, ids, match, p_show, p_episode, t_item, **kwargs):
        # Process episode
        if match.media == GuidMatch.Media.Episode:
            # Process episode
            self.execute_handlers(
                mode, SyncMedia.Episodes, data,
                key=ids['episode'],

                p_item=p_episode,
                t_item=t_item,
                **kwargs
            )

            return True

        # Process movie
        if match.media == GuidMatch.Media.Movie:
            # Build movie item from plex episode
            p_movie = p_episode.copy()

            p_movie['title'] = p_show.get('title')
            p_movie['year'] = p_show.get('year')

            # Process movie
            self.execute_handlers(
                mode, SyncMedia.Movies, data,
                key=ids['episode'],

                p_item=p_episode,
                t_item=t_item,
                **kwargs
            )
            return True

        raise ValueError('Unknown media type: %r' % (match.media,))

    @elapsed.clock
    def execute_handlers(self, mode, media, data, *args, **kwargs):
        if type(media) is not list:
            media = [media]

        if type(data) is not list:
            data = [data]

        for m, d in itertools.product(media, data):
            if d not in self.handlers:
                log.debug('Unable to find handler for data: %r', d)
                continue

            try:
                self.handlers[d].run(m, mode, *args, **kwargs)
            except Exception as ex:
                log.warn('Exception raised in handlers[%r].run(%r, ...): %s', d, m, ex, exc_info=True)

    def get_enabled_data(self):
        config = self.configuration

        # Determine accepted modes
        modes = [SyncMode.Full]

        if self.mode == SyncMode.Full:
            modes.extend([
                SyncMode.FastPull,
                SyncMode.Pull,
                SyncMode.Push
            ])
        elif self.mode == SyncMode.FastPull:
            modes.extend([
                self.mode,
                SyncMode.Pull
            ])
        else:
            modes.append(self.mode)

        # Retrieve enabled data
        result = []

        if config['sync.watched.mode'] in modes:
            result.append(SyncData.Watched)

        if config['sync.ratings.mode'] in modes:
            result.append(SyncData.Ratings)

        if config['sync.playback.mode'] in modes:
            result.append(SyncData.Playback)

        if config['sync.collection.mode'] in modes:
            result.append(SyncData.Collection)

        # Lists
        if config['sync.lists.watchlist.mode'] in modes:
            result.append(SyncData.Watchlist)

        if config['sync.lists.liked.mode'] in modes:
            result.append(SyncData.Liked)

        if config['sync.lists.personal.mode'] in modes:
            result.append(SyncData.Personal)

        # Filter `result` to data provided by this mode
        if self.data is None:
            log.warn('No "data" property defined on %r', self)
            return result

        if self.data == SyncData.All:
            return result

        return [
            data for data in result
            if data in self.data
        ]

    def get_data(self, media):
        for data in TRAKT_DATA_MAP[media]:
            if not self.is_data_enabled(data):
                continue

            yield data

    @elapsed.clock
    def is_data_enabled(self, data):
        return data in self.enabled_data

    def run_episode_action(self, mode, data, ids, match, p_show, p_episode, t_item, **kwargs):
        if match.media == GuidMatch.Media.Movie:
            # Process movie
            self.execute_episode_action(
                mode, data, ids, match,
                p_show, p_episode, t_item,
                **kwargs
            )
        elif match.media == GuidMatch.Media.Episode:
            # Ensure `match` contains episodes
            if not match.episodes:
                log.info('No episodes returned for: %s/%s', match.guid.service, match.guid.id)
                return

            # Process each episode
            for season_num, episode_num in match.episodes:
                t_season = self._get_show_season(t_item, season_num)

                if t_season is None:
                    # Unable to find matching season in `t_show`
                    continue

                t_episode = self._get_season_episode(t_season, episode_num)

                if t_episode is None:
                    # Unable to find matching episode in `t_season`
                    continue

                self.execute_episode_action(
                    mode, data, ids, match,
                    p_show, p_episode, t_episode,
                    **kwargs
                )

    def sections(self, section_type=None):
        # Retrieve "section" for current task
        section_key = self.current.kwargs.get('section', None)

        # Fetch sections from server
        p_sections = Plex['library'].sections()

        if p_sections is None:
            return None

        # Filter sections, map to dictionary
        result = {}

        for section in p_sections.filter(section_type, section_key):
            # Apply section name filter
            if not Filters.is_valid_section_name(section.title):
                continue

            try:
                key = int(section.key)
            except Exception as ex:
                log.warn('Unable to cast section key %r to integer: %s', section.key, ex, exc_info=True)
                continue

            result[key] = section.uuid

        return [(key, ) for key in result.keys()], result

    @staticmethod
    def _get_show_season(t_show, season_num):
        if type(t_show) is dict:
            return t_show.get('seasons', {}).get(season_num)

        return t_show.seasons.get(season_num)

    @staticmethod
    def _get_season_episode(t_season, episode_num):
        if type(t_season) is dict:
            return t_season.get('episodes', {}).get(episode_num)

        return t_season.episodes.get(episode_num)
