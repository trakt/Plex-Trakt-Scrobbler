from plugin.sync.core.enums import SyncMode, SyncMedia
from plugin.sync.modes.core.base import Mode, TRAKT_DATA_MAP

from plex_database.models import LibrarySectionType, LibrarySection
import logging

log = logging.getLogger(__name__)


class Movies(Mode):
    mode = SyncMode.Pull

    def run(self):
        # Retrieve movie sections
        p_sections = self.plex.library.sections(
            LibrarySectionType.Movie,
            LibrarySection.id
        ).tuples()

        # Fetch movies with account settings
        # TODO use actual `account`
        p_items = self.plex.library.movies.mapped(
            p_sections,
            account=1,
            parse_guid=True
        )

        for rating_key, p_guid, p_item in p_items:
            key = (p_guid.agent, p_guid.sid)

            # Try retrieve `pk` for `key`
            pk = self.trakt.table.get(key)

            if pk is None:
                # No `pk` found
                continue

            for data in TRAKT_DATA_MAP[SyncMedia.Movies]:
                t_items = self.trakt[(SyncMedia.Movies, data)]
                t_item = t_items.get(pk)

                self.execute_handlers(
                    SyncMedia.Movies, data,
                    rating_key=rating_key,

                    p_item=p_item,
                    t_item=t_item
                )


class Shows(Mode):
    mode = SyncMode.Pull

    def run(self):
        # Retrieve show sections
        p_sections = self.plex.library.sections(
            LibrarySectionType.Show,
            LibrarySection.id
        ).tuples()

        # Fetch episodes with account settings
        # TODO use actual `account`
        p_shows, p_seasons, p_episodes = self.plex.library.episodes.mapped(
            p_sections,
            account=1,
            parse_guid=True
        )

        # TODO process shows, seasons

        # Process episodes
        for ids, p_guid, (season_num, episode_num), p_item in p_episodes:
            key = (p_guid.agent, p_guid.sid)

            # Try retrieve `pk` for `key`
            pk = self.trakt.table.get(key)

            if pk is None:
                # No `pk` found
                continue

            if not ids.get('episode'):
                # Missing `episode` rating key
                continue

            for data in TRAKT_DATA_MAP[SyncMedia.Episodes]:
                t_show = self.trakt[(SyncMedia.Episodes, data)].get(pk)

                if t_show is None:
                    # Unable to find matching show in trakt data
                    continue

                t_season = t_show.seasons.get(season_num)

                if t_season is None:
                    # Unable to find matching season in `t_show`
                    continue

                t_episode = t_season.episodes.get(episode_num)

                if t_episode is None:
                    # Unable to find matching episode in `t_season`
                    continue

                self.execute_handlers(
                    SyncMedia.Episodes, data,
                    rating_key=ids['episode'],

                    p_item=p_item,
                    t_item=t_episode
                )


class Pull(Mode):
    mode = SyncMode.Pull

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

        # Flush caches to archives
        self.current.state.flush()
