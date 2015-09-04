from plugin.sync.core.constants import GUID_AGENTS
from plugin.sync.core.enums import SyncMode, SyncMedia, SyncData
from plugin.sync.modes.core.base import Mode, log_unsupported_guid

from plex_database.models import MetadataItem, MediaItem, Episode
from plex_metadata import Guid
import copy
import logging

log = logging.getLogger(__name__)


class Base(Mode):
    mode = SyncMode.Push


class Movies(Base):
    def run(self):
        # Retrieve movie sections
        p_sections = self.sections('movie')

        # Fetch movies with account settings
        p_items = self.plex.library.movies.mapped(
            p_sections, [
                MetadataItem.added_at,
                MetadataItem.title,
                MetadataItem.year,

                MediaItem.audio_channels,
                MediaItem.audio_codec,
                MediaItem.height,
                MediaItem.interlaced
            ],
            account=self.current.account.plex.key,
            parse_guid=True
        )

        # Task started
        pending_movies = self.trakt.movies.copy()
        unsupported_movies = {}

        # Iterate over plex movies
        for rating_key, p_guid, p_item in p_items:
            if not p_guid or p_guid.agent not in GUID_AGENTS:
                log_unsupported_guid(log, rating_key, p_guid, p_item, unsupported_movies)
                continue

            key = (p_guid.agent, p_guid.sid)

            # Try retrieve `pk` for `key`
            pk = self.trakt.table.get(key)

            for data in self.get_data(SyncMedia.Movies):
                t_movie = self.trakt[(SyncMedia.Movies, data)].get(pk)

                self.execute_handlers(
                    SyncMedia.Movies, data,

                    key=rating_key,

                    p_guid=p_guid,
                    p_item=p_item,

                    t_item=t_movie
                )

            # Remove movie from `pending` set
            if pk and pk in pending_movies:
                pending_movies.remove(pk)

            # Task checkpoint
            self.checkpoint()

        # Iterate over trakt movies (that aren't in plex)
        log.debug('Pending movies: %r', pending_movies)

        for pk in list(pending_movies):
            triggered = False

            # Iterate over data handlers
            for data in self.get_data(SyncMedia.Movies):
                # Retrieve movie
                t_movie = self.trakt[(SyncMedia.Movies, data)].get(pk)

                if not t_movie:
                    continue

                log.info('Found movie missing from plex: %r [data: %r]', pk, SyncData.title(data))

                # Trigger handler
                self.execute_handlers(
                    SyncMedia.Movies, data,

                    key=None,

                    p_guid=Guid(*pk),
                    p_item=None,

                    t_item=t_movie
                )

                # Mark triggered
                triggered = True

            # Check if action was triggered
            if not triggered:
                log.info('Unable to find movie: %r', pk)
                continue

            # Remove movie from `pending` set
            pending_movies.remove(pk)

        log.debug('Pending movies: %r', pending_movies)


class Shows(Base):
    def run(self):
        # Retrieve movie sections
        p_sections = self.sections('show')

        # Fetch movies with account settings
        p_shows, p_seasons, p_episodes = self.plex.library.episodes.mapped(
            p_sections, ([
                MetadataItem.title,
                MetadataItem.year
            ], [], [
                MediaItem.audio_channels,
                MediaItem.audio_codec,
                MediaItem.height,
                MediaItem.interlaced,

                Episode.added_at
            ]),
            account=self.current.account.plex.key,
            parse_guid=True
        )

        # Task started
        pending_shows = self.trakt.shows.copy()
        pending_episodes = copy.deepcopy(self.trakt.episodes)

        unsupported_shows = {}

        log.debug('Pending shows: %r', pending_shows)
        log.debug('Pending episodes: %r', pending_episodes)

        # TODO process seasons

        # Iterate over plex shows
        for sh_id, p_guid, p_show in p_shows:
            if not p_guid or p_guid.agent not in GUID_AGENTS:
                log_unsupported_guid(log, sh_id, p_guid, p_show, unsupported_shows)
                continue

            key = (p_guid.agent, p_guid.sid)

            # Try retrieve `pk` for `key`
            pk = self.trakt.table.get(key)

            for data in self.get_data(SyncMedia.Shows):
                t_show = self.trakt[(SyncMedia.Shows, data)].get(pk)

                # Execute show handlers
                self.execute_handlers(
                    SyncMedia.Shows, data,
                    key=sh_id,
                    p_guid=p_guid,

                    p_item=p_show,

                    t_item=t_show
                )

            # Remove show from `pending_shows`
            if pk and pk in pending_shows:
                pending_shows.remove(pk)

            # Task checkpoint
            self.checkpoint()

        # Iterate over plex episodes
        for ids, p_guid, (season_num, episode_num), p_show, p_season, p_episode in p_episodes:
            if not p_guid or p_guid.agent not in GUID_AGENTS:
                log_unsupported_guid(log, ids['show'], p_guid, p_show, unsupported_shows)
                continue

            key = (p_guid.agent, p_guid.sid)
            identifier = (season_num, episode_num)

            # Try retrieve `pk` for `key`
            pk = self.trakt.table.get(key)

            for data in self.get_data(SyncMedia.Episodes):
                t_show, t_season, t_episode = self.t_objects(
                    self.trakt[(SyncMedia.Episodes, data)], pk,
                    season_num, episode_num
                )

                # Execute episode handlers
                self.execute_handlers(
                    SyncMedia.Episodes, data,

                    key=ids['episode'],
                    identifier=identifier,

                    p_guid=p_guid,
                    p_show=p_show,
                    p_item=p_episode,

                    t_show=t_show,
                    t_item=t_episode
                )

            # Remove episode from `pending_episodes`
            if pk in pending_episodes and identifier in pending_episodes[pk]:
                pending_episodes[pk].remove(identifier)

            # Task checkpoint
            self.checkpoint()

        # Iterate over trakt shows (that aren't in plex)
        log.debug('Pending shows: %r', pending_shows)

        for pk in list(pending_shows):
            triggered = False

            # Iterate over data handlers
            for data in self.get_data(SyncMedia.Shows):
                # Retrieve movie
                t_show = self.trakt[(SyncMedia.Shows, data)].get(pk)

                if not t_show:
                    continue

                log.info('Found show missing from plex: %r [data: %r]', pk, SyncData.title(data))

                # Trigger handler
                self.execute_handlers(
                    SyncMedia.Shows, data,

                    key=None,

                    p_guid=Guid(*pk),
                    p_item=None,

                    t_item=t_show
                )

                # Mark triggered
                triggered = True

            # Check if action was triggered
            if not triggered:
                log.info('Unable to find show: %r', pk)
                continue

            # Remove movie from `pending` set
            pending_shows.remove(pk)

        log.debug('Pending shows: %r', pending_shows)

        # Iterate over trakt episodes (that aren't in plex)
        log.debug('Pending episodes: %r', pending_episodes)

        for pk, episodes in [(p, list(e)) for (p, e) in pending_episodes.items()]:
            # Iterate over trakt episodes (that aren't in plex)
            for identifier in episodes:
                season_num, episode_num = identifier

                triggered = False

                # Iterate over data handlers
                for data in self.get_data(SyncMedia.Episodes):
                    t_show, t_season, t_episode = self.t_objects(
                        self.trakt[(SyncMedia.Episodes, data)], pk,
                        season_num, episode_num
                    )

                    if not t_episode:
                        continue

                    log.debug('Found episode missing from plex: %r - %r [data: %r]', pk, identifier, SyncData.title(data))

                    # Trigger handler
                    self.execute_handlers(
                        SyncMedia.Episodes, data,
                        key=None,
                        identifier=identifier,
                        p_guid=Guid(*pk),

                        p_show=None,
                        p_item=None,

                        t_show=t_show,
                        t_item=t_episode
                    )

                    # Mark triggered
                    triggered = True

                # Check if action was triggered
                if not triggered:
                    log.info('Unable to find episode: %r - %r', pk, identifier)
                    continue

                # Remove movie from `pending` set
                pending_episodes[pk].remove(identifier)

        log.debug('Pending episodes: %r', pending_episodes)

    @staticmethod
    def t_objects(collection, pk, season_num, episode_num):
        # Try find trakt `Show` from `collection`
        t_show = collection.get(pk)

        if t_show is None:
            return t_show, None, None

        # Try find trakt `Season`
        t_season = t_show.seasons.get(season_num)

        if t_season is None:
            return t_show, t_season, None

        # Try find trakt `Episode`
        t_episode = t_season.episodes.get(episode_num)

        return t_show, t_season, t_episode


class Push(Mode):
    mode = SyncMode.Push

    children = [
        Movies,
        Shows
    ]

    def run(self):
        # Fetch changes from trakt.tv
        self.trakt.refresh()

        # Build key table for lookups
        self.trakt.build_table()

        # Run children
        self.execute_children()

        # Send artifacts to trakt
        self.current.artifacts.send()
