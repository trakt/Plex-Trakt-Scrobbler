from plugin.sync.core.enums import SyncData, SyncMedia
from plugin.sync.core.guid import GuidParser
from plugin.sync.modes.core.base import log_unsupported, mark_unsupported
from plugin.sync.modes.fast_pull.base import Base

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
        for mo_id, guid, p_movie in self.p_movies:
            # Increment one step
            self.current.progress.group(Movies).step()

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

            # Iterate over changed data
            for data, action, t_movie in self.iter_changes(SyncMedia.Movies, pk):
                self.execute_handlers(
                    SyncMedia.Movies, data,
                    action=action,
                    key=mo_id,

                    p_item=p_movie,
                    t_item=t_movie
                )

            # Task checkpoint
            self.checkpoint()

        # Stop progress group
        self.current.progress.group(Movies).stop()

        # Log details
        log_unsupported(log, 'Found %d unsupported movie(s)', self.p_unsupported)
