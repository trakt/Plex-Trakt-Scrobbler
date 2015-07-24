from plugin.sync.core.constants import GUID_AGENTS
from plugin.sync.core.enums import SyncMode, SyncMedia
from plugin.sync.modes.core.base import Mode, log_unsupported_guid

from plex_database.models import LibrarySectionType, MetadataItem, MediaItem, Episode
import logging

log = logging.getLogger(__name__)


class Base(Mode):
    mode = SyncMode.Push


class Movies(Base):
    def run(self):
        # Retrieve movie sections
        p_sections = self.sections(LibrarySectionType.Movie)

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
            account=self.current.account.plex.id,
            parse_guid=True
        )

        # Task started
        unsupported_movies = {}

        for rating_key, p_guid, p_item in p_items:
            if p_guid.agent not in GUID_AGENTS:
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

            # Task checkpoint
            self.checkpoint()


class Shows(Base):
    def run(self):
        # Retrieve movie sections
        p_sections = self.sections(LibrarySectionType.Show)

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
            account=self.current.account.plex.id,
            parse_guid=True
        )

        # Task started
        unsupported_shows = {}

        # TODO process seasons

        # Process shows
        for sh_id, p_guid, p_show in p_shows:
            if p_guid.agent not in GUID_AGENTS:
                log_unsupported_guid(log, sh_id, p_guid, p_show, unsupported_shows)
                continue

            key = (p_guid.agent, p_guid.sid)

            # Try retrieve `pk` for `key`
            pk = self.trakt.table.get(key)

            for data in self.get_data(SyncMedia.Shows):
                # Retrieve trakt show
                t_show = self.trakt[(SyncMedia.Shows, data)].get(pk)

                # Execute episode handlers
                self.execute_handlers(
                    SyncMedia.Shows, data,

                    key=sh_id,

                    p_guid=p_guid,
                    p_item=p_show,

                    t_item=t_show
                )

        # Process episodes
        for ids, p_guid, (season_num, episode_num), p_show, p_season, p_episode in p_episodes:
            if p_guid.agent not in GUID_AGENTS:
                log_unsupported_guid(log, ids['show'], p_guid, p_show, unsupported_shows)
                continue

            key = (p_guid.agent, p_guid.sid)

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
                    identifier=(season_num, episode_num),

                    p_guid=p_guid,
                    p_show=p_show,
                    p_item=p_episode,

                    t_show=t_show,
                    t_item=t_episode
                )

            # Task checkpoint
            self.checkpoint()

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
