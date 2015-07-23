from plugin.sync.core.constants import GUID_AGENTS
from plugin.sync.core.enums import SyncMode, SyncMedia
from plugin.sync.modes.core.base import Mode, log_unsupported_guid

from plex_database.models import LibrarySectionType
from trakt_sync.cache.main import Cache
import logging

log = logging.getLogger(__name__)


class Movies(Mode):
    mode = SyncMode.FastPull

    def run(self):
        # Retrieve movie sections
        p_sections = self.sections(LibrarySectionType.Movie)

        # Fetch movies with account settings
        p_items = self.plex.library.movies.mapped(
            p_sections,
            account=self.current.account.plex.id,
            parse_guid=True
        )

        # Calculate total number of steps
        total = 0

        for (media, data), result in self.trakt.changes:
            if media != SyncMedia.Movies:
                # Ignore changes that aren't for episodes
                continue

            data_name = Cache.Data.get(data)

            for count in result.metrics.movies.get(data_name, {}).itervalues():
                total += count

        # Task started
        unsupported_movies = {}

        self.current.progress.start(total)

        # Process movies
        for rating_key, p_guid, p_item in p_items:
            if p_guid.agent not in GUID_AGENTS:
                log_unsupported_guid(log, rating_key, p_guid, p_item, unsupported_movies)
                continue

            key = (p_guid.agent, p_guid.sid)

            # Try retrieve `pk` for `key`
            pk = self.trakt.table.get(key)

            if pk is None:
                # No `pk` found
                continue

            for (media, data), result in self.trakt.changes:
                if media != SyncMedia.Movies:
                    # Ignore changes that aren't for movies
                    continue

                if not self.is_data_enabled(data):
                    # Data type has been disabled
                    continue

                data_name = Cache.Data.get(data)

                if data_name not in result.changes:
                    # No changes for collection
                    continue

                for action, items in result.changes[data_name].items():
                    t_item = items.get(pk)

                    if t_item is None:
                        # No item found in changes
                        continue

                    self.execute_handlers(
                        SyncMedia.Movies, data,
                        action=action,
                        key=rating_key,

                        p_item=p_item,
                        t_item=t_item
                    )

                    # Increment one step
                    self.current.progress.step()

            # Task checkpoint
            self.checkpoint()

        # Task stopped
        self.current.progress.stop()


class Shows(Mode):
    mode = SyncMode.FastPull

    def run(self):
        # Retrieve show sections
        p_sections = self.sections(LibrarySectionType.Show)

        # Fetch episodes with account settings
        p_shows, p_seasons, p_episodes = self.plex.library.episodes.mapped(
            p_sections,
            account=self.current.account.plex.id,
            parse_guid=True
        )

        # TODO process shows, seasons

        # Calculate total number of episode changes
        total = 0

        for (media, data), result in self.trakt.changes:
            if media != SyncMedia.Episodes:
                # Ignore changes that aren't for episodes
                continue

            data_name = Cache.Data.get(data)

            for count in result.metrics.episodes.get(data_name, {}).itervalues():
                total += count

        # Task started
        unsupported_shows = {}

        self.current.progress.start(total)

        # Process episodes
        for ids, p_guid, (season_num, episode_num), p_show, p_season, p_episode in p_episodes:
            if p_guid.agent not in GUID_AGENTS:
                log_unsupported_guid(log, ids['show'], p_guid, p_show, unsupported_shows)
                continue

            key = (p_guid.agent, p_guid.sid)

            # Try retrieve `pk` for `key`
            pk = self.trakt.table.get(key)

            if pk is None:
                # No `pk` found
                continue

            if not ids.get('episode'):
                # Missing `episode` rating key
                continue

            for (media, data), result in self.trakt.changes:
                if media != SyncMedia.Episodes:
                    # Ignore changes that aren't for episodes
                    continue

                if not self.is_data_enabled(data):
                    # Data type has been disabled
                    continue

                data_name = Cache.Data.get(data)

                if data_name not in result.changes:
                    # No changes for collection
                    continue

                for action, shows in result.changes[data_name].items():
                    t_show = shows.get(pk)

                    if t_show is None:
                        # Unable to find matching show in trakt data
                        continue

                    t_season = t_show.get('seasons', {}).get(season_num)

                    if t_season is None:
                        # Unable to find matching season in `t_show`
                        continue

                    t_episode = t_season.get('episodes', {}).get(episode_num)

                    if t_episode is None:
                        # Unable to find matching episode in `t_season`
                        continue

                    self.execute_handlers(
                        SyncMedia.Episodes, data,
                        action=action,
                        key=ids['episode'],

                        p_item=p_episode,
                        t_item=t_episode
                    )

                    # Increment one step
                    self.current.progress.step()

            # Task checkpoint
            self.checkpoint()

        # Task stopped
        self.current.progress.stop()


class FastPull(Mode):
    mode = SyncMode.FastPull

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
