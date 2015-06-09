from plugin.sync.core.enums import SyncMode, SyncMedia
from plugin.sync.modes.core.base import Mode, TRAKT_DATA_MAP

from plex_database.models import LibrarySectionType, LibrarySection, MetadataItem, MediaItem
import logging

log = logging.getLogger(__name__)


class Base(Mode):
    mode = SyncMode.Pull


class Movies(Base):
    def run(self):
        # Retrieve movie sections
        p_sections = self.plex.library.sections(
            LibrarySectionType.Movie,
            LibrarySection.id
        ).tuples()

        # Fetch movies with account settings
        p_items = self.plex.library.movies.mapped(
            p_sections, [
                MetadataItem.title,
                MetadataItem.year
            ],
            account=self.current.account.plex.id,
            parse_guid=True
        )

        # Task started
        for rating_key, p_guid, p_item in p_items:
            key = (p_guid.agent, p_guid.sid)

            # Try retrieve `pk` for `key`
            pk = self.trakt.table.get(key)

            for data in TRAKT_DATA_MAP[SyncMedia.Movies]:
                t_movie = self.trakt[(SyncMedia.Movies, data)].get(pk)

                self.execute_handlers(
                    SyncMedia.Movies, data,

                    key=rating_key,

                    p_guid=p_guid,
                    p_item=p_item,

                    t_item=t_movie
                )


class Shows(Base):
    def run(self):
        # Retrieve movie sections
        p_sections = self.plex.library.sections(
            LibrarySectionType.Show,
            LibrarySection.id
        ).tuples()

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

                MetadataItem.added_at
            ]),
            account=self.current.account.plex.id,
            parse_guid=True
        )

        # Task started

        # TODO process shows, seasons

        # Process episodes
        for ids, p_guid, (season_num, episode_num), p_show, p_season, p_episode in p_episodes:
            key = (p_guid.agent, p_guid.sid)

            # Try retrieve `pk` for `key`
            pk = self.trakt.table.get(key)

            for data in TRAKT_DATA_MAP[SyncMedia.Episodes]:
                t_show, t_season, t_episode = self.t_objects(
                    self.trakt[(SyncMedia.Episodes, data)], pk,
                    season_num, episode_num
                )

                self.execute_handlers(
                    SyncMedia.Episodes, data,

                    key=ids['episode'],
                    season_num=season_num,
                    episode_num=episode_num,

                    p_guid=p_guid,
                    p_show=p_show,
                    p_item=p_episode,

                    t_show=t_show,
                    t_item=t_episode
                )

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
