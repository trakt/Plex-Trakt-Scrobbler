from plugin.sync.core.enums import SyncData, SyncMedia
from plugin.sync.core.guid import GuidParser
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

    def __init__(self, task):
        super(Movies, self).__init__(task)

        # Sections
        self.p_sections = None
        self.p_sections_map = None

        # Movies
        self.p_movies = None

        self.p_pending = None
        self.p_unsupported = None

    @elapsed.clock
    def construct(self):
        # Retrieve movie sections
        self.p_sections, self.p_sections_map = self.sections('movie')

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

        # Calculate total number of movies
        self.p_pending = {}

        for data in self.get_data(SyncMedia.Movies):
            if data not in self.p_pending:
                self.p_pending[data] = {}

            for pk in self.trakt[(SyncMedia.Movies, data)]:
                self.p_pending[data][pk] = False

        # Reset state
        self.p_unsupported = {}

    @elapsed.clock
    def run(self):
        for mo_id, guid, p_movie in self.p_movies:
            # Parse guid
            match = GuidParser.parse(guid)

            if not match.supported:
                mark_unsupported(self.p_unsupported, mo_id, guid)
                continue

            if not match.found:
                log.info('Unable to find identifier for: %s/%s (rating_key: %r)', guid.service, guid.id, mo_id)
                continue

            key = (match.guid.service, match.guid.id)

            # Try retrieve `pk` for `key`
            pk = self.trakt.table('movies').get(key)

            # Store in item map
            self.current.map.add(p_movie.get('library_section'), mo_id, [key, pk])

            if pk is None:
                # No `pk` found
                continue

            # Execute data handlers
            for data in self.get_data(SyncMedia.Movies):
                t_movie = self.trakt[(SyncMedia.Movies, data)].get(pk)

                self.execute_handlers(
                    self.mode, SyncMedia.Movies, data,
                    key=mo_id,

                    p_item=p_movie,
                    t_item=t_movie
                )

                # Increment one step
                self.step(self.p_pending, data, pk)

            # Task checkpoint
            self.checkpoint()

        # Log details
        log_unsupported(log, 'Found %d unsupported movie(s)', self.p_unsupported)
        log.debug('Pending: %r', self.p_pending)
