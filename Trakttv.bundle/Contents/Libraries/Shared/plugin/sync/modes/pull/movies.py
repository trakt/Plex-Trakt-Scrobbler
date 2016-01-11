from plugin.sync.core.constants import GUID_AGENTS
from plugin.sync.core.enums import SyncMedia
from plugin.sync.modes.core.base import log_unsupported, mark_unsupported
from plugin.sync.modes.pull.base import Base

from plex_database.models import MetadataItem
import elapsed
import logging

log = logging.getLogger(__name__)


class Movies(Base):
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

        # Calculate total number of movies
        pending = {}
        total = 0

        for data in self.get_data(SyncMedia.Movies):
            if data not in pending:
                pending[data] = {}

            for pk in self.trakt[(SyncMedia.Movies, data)]:
                pending[data][pk] = False
                total += 1

        # Task started
        unsupported_movies = {}

        self.current.progress.start(total)

        for rating_key, p_guid, p_item in p_items:
            if not p_guid or p_guid.agent not in GUID_AGENTS:
                mark_unsupported(unsupported_movies, rating_key, p_guid, p_item)
                continue

            key = (p_guid.agent, p_guid.sid)

            # Try retrieve `pk` for `key`
            pk = self.trakt.table.get(key)

            # Store in item map
            self.current.map.add(p_item.get('library_section'), rating_key, [key, pk])

            if pk is None:
                # No `pk` found
                continue

            # Execute data handlers
            for data in self.get_data(SyncMedia.Movies):
                t_movie = self.trakt[(SyncMedia.Movies, data)].get(pk)

                self.execute_handlers(
                    SyncMedia.Movies, data,
                    key=rating_key,

                    p_item=p_item,
                    t_item=t_movie
                )

                # Increment one step
                self.step(pending, data, pk)

            # Task checkpoint
            self.checkpoint()

        # Log details
        log_unsupported(log, 'Found %d unsupported movie(s)\n%s', unsupported_movies)
        log.debug('Pending: %r', pending)

        # Task stopped
        self.current.progress.stop()
