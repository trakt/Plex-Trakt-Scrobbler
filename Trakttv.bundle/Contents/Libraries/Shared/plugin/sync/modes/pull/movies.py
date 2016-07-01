from plugin.core.constants import GUID_SERVICES
from plugin.sync.core.enums import SyncData, SyncMedia
from plugin.sync.modes.core.base import log_unsupported, mark_unsupported
from plugin.sync.modes.pull.base import Base

from plex_database.models import MetadataItem
import elapsed
import logging

log = logging.getLogger(__name__)


class Movies(Base):
    data = [
        SyncData.Collection,
        SyncData.Playback,
        SyncData.Ratings,
        SyncData.Watched
    ]

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

        for data in self.get_data(SyncMedia.Movies):
            if data not in pending:
                pending[data] = {}

            for pk in self.trakt[(SyncMedia.Movies, data)]:
                pending[data][pk] = False

        # Task started
        unsupported_movies = {}

        for mo_id, p_guid, p_item in p_items:
            # Process `p_guid` (map + validate)
            supported, p_guid = self.process_guid(p_guid)

            if not supported:
                mark_unsupported(unsupported_movies, mo_id, p_guid)
                continue

            key = (p_guid.service, p_guid.id)

            # Try retrieve `pk` for `key`
            pk = self.trakt.table('movies').get(key)

            # Store in item map
            self.current.map.add(p_item.get('library_section'), mo_id, [key, pk])

            if pk is None:
                # No `pk` found
                continue

            # Execute data handlers
            for data in self.get_data(SyncMedia.Movies):
                t_movie = self.trakt[(SyncMedia.Movies, data)].get(pk)

                self.execute_handlers(
                    SyncMedia.Movies, data,
                    key=mo_id,

                    p_item=p_item,
                    t_item=t_movie
                )

                # Increment one step
                self.step(pending, data, pk)

            # Task checkpoint
            self.checkpoint()

        # Log details
        log_unsupported(log, 'Found %d unsupported movie(s)', unsupported_movies)
        log.debug('Pending: %r', pending)
