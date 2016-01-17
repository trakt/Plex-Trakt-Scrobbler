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

    def __init__(self, task):
        super(Movies, self).__init__(task)

        # Sections
        self.p_sections = None
        self.p_sections_map = None

        # Items
        self.p_count = None
        self.p_movies = None

        self.p_unsupported = None

    @elapsed.clock
    def construct(self):
        # Retrieve movie sections
        self.p_sections, self.p_sections_map = self.sections('movie')

        # Determine number of movies that will be processed
        self.p_count = self.plex.library.movies.count(
            self.p_sections,
            account=self.current.account.plex.key
        )

        # Increment progress steps total
        self.current.progress.group(Movies).add(self.p_count)

    @elapsed.clock
    def start(self):
        # Fetch movies with account settings
        self.p_movies = self.plex.library.movies.mapped(
            self.p_sections, [
                MetadataItem.library_section
            ],
            account=self.current.account.plex.key,
            parse_guid=True
        )

        # Reset state
        self.p_unsupported = {}

    @elapsed.clock
    def run(self):
        # Process movies
        for mo_id, guid, p_item in self.p_movies:
            # Increment one step
            self.current.progress.group(Movies).step()

            # Ensure `guid` is available
            if not guid or guid.agent not in GUID_AGENTS:
                mark_unsupported(self.p_unsupported, mo_id, guid, p_item)
                continue

            key = (guid.agent, guid.sid)

            log.debug('Processing movie: %s', key)

            # Try retrieve `pk` for `key`
            pk = self.trakt.table.get(key)

            # Store in item map
            self.current.map.add(p_item.get('library_section'), mo_id, [key, pk])

            if pk is None:
                # No `pk` found
                continue

            # Iterate over changed data
            for key, result in self.trakt.changes:
                media, data = key[0:2]

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
                        key=mo_id,

                        p_item=p_item,
                        t_item=t_item
                    )

            # Task checkpoint
            self.checkpoint()

        # Stop progress group
        self.current.progress.group(Movies).stop()

        # Log details
        log_unsupported(log, 'Found %d unsupported movie(s)\n%s', self.p_unsupported)
