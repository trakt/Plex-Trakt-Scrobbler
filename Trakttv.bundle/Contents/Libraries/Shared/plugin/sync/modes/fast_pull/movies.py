from plugin.sync.core.constants import GUID_AGENTS
from plugin.sync.core.enums import SyncMode, SyncData, SyncMedia
from plugin.sync.modes.core.base import Mode, log_unsupported, mark_unsupported

from plex_database.models import MetadataItem
from trakt_sync.cache.main import Cache
import elapsed
import logging

log = logging.getLogger(__name__)


class Movies(Mode):
    mode = SyncMode.FastPull

    @elapsed.clock
    def run(self):
        # Retrieve movie sections
        p_sections, p_sections_map = self.sections('movie')

        # Fetch movies with account settings
        p_items = self.plex.library.movies.mapped(
            p_sections, [
                MetadataItem.library_section
            ],
            account=self.current.account.plex.key,
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
            if not p_guid or p_guid.agent not in GUID_AGENTS:
                mark_unsupported(unsupported_movies, rating_key, p_guid, p_item)
                continue

            key = (p_guid.agent, p_guid.sid)

            # Try retrieve `pk` for `key`
            pk = self.trakt.table.get(key)

            if pk is None:
                # No `pk` found
                continue

            # Store in item map
            self.current.map.add(p_item.get('library_section'), rating_key, p_guid)

            # Iterate over changed data
            for (media, data), result in self.trakt.changes:
                if media != SyncMedia.Movies:
                    # Ignore changes that aren't for movies
                    continue

                if data == SyncData.Watchlist:
                    # Ignore watchlist data
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

        # Log details
        log_unsupported(log, 'Found %d unsupported movie(s)\n%s', unsupported_movies)

        # Task stopped
        self.current.progress.stop()
