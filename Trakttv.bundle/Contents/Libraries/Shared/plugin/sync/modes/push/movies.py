from plugin.sync.core.enums import SyncMedia, SyncData
from plugin.sync.core.guid import GuidParser
from plugin.sync.modes.core.base import log_unsupported, mark_unsupported
from plugin.sync.modes.push.base import Base

from plex_database.models import MetadataItem, MediaItem
from plex_metadata import Guid
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
        self.current.progress.group(Movies, 'matched:movies').add(self.p_count)
        self.current.progress.group(Movies, 'missing:movies')

    @elapsed.clock
    def start(self):
        # Fetch movies with account settings
        self.p_movies = self.plex.library.movies.mapped(
            self.p_sections, [
                MetadataItem.added_at,
                MetadataItem.title,
                MetadataItem.year,

                MediaItem.audio_channels,
                MediaItem.audio_codec,
                MediaItem.height,
                MediaItem.interlaced
            ],
            account=self.current.account.plex.key,
            parse_guid=True
        )

        # Update pending item collections
        self.current.pending.create('movies', self.trakt.table.movie_keys.copy())

        # Reset state
        self.p_unsupported = {}

    @elapsed.clock
    def run(self):
        for mo_id, guid, p_item in self.p_movies:
            # Increment one step
            self.current.progress.group(Movies, 'matched:movies').step()

            # Parse guid
            match = GuidParser.parse(guid)

            if not match.supported:
                mark_unsupported(self.p_unsupported, mo_id, guid)
                continue

            if not match.found:
                log.info('Unable to find identifier for: %s/%s (rating_key: %r)', guid.service, guid.id, mo_id)
                continue

            # Retrieve primary key for item
            pk = self.trakt.table('movies').get((match.guid.service, match.guid.id))

            # Process movie (execute handlers)
            self.execute_movie(mo_id, pk, match.guid, p_item)

            # Remove movie from pending items collection
            self.current.pending['movies'].remove(pk)

            # Task checkpoint
            self.checkpoint()

        # Stop progress group
        self.current.progress.group(Movies, 'matched:movies').stop()

        # Report unsupported movies (unsupported guid)
        log_unsupported(log, 'Found %d unsupported movie(s)', self.p_unsupported)

    @elapsed.clock
    def finish(self):
        if self.current.kwargs.get('section'):
            # Collection cleaning disabled for individual syncs
            return

        # Increment progress steps
        self.current.progress.group(Movies, 'missing:movies').add(len(self.current.pending['movies'].keys))

        # Iterate over movies
        for pk in list(self.current.pending['movies'].keys):
            # Increment one step
            self.current.progress.group(Movies, 'missing:movies').step()

            # Iterate over data handlers
            triggered = False

            for data in self.get_data(SyncMedia.Movies):
                if data not in [SyncData.Collection]:
                    continue

                # Retrieve movie
                t_movie = self.trakt[(SyncMedia.Movies, data)].get(pk)

                if not t_movie:
                    continue

                log.debug('Found movie missing from plex: %r [data: %r]', pk, SyncData.title(data))

                # Trigger handler
                self.execute_handlers(
                    self.mode, SyncMedia.Movies, data,

                    key=None,

                    guid=Guid.construct(*pk, matched=True),
                    p_item=None,

                    t_item=t_movie
                )

                # Mark triggered
                triggered = True

            # Check if action was triggered
            if not triggered:
                continue

            # Remove movie from `pending` set
            self.current.pending['movies'].keys.remove(pk)

        # Stop progress group
        self.current.progress.group(Movies, 'missing:movies').stop()

        # Report pending movies (no actions triggered)
        self.log_pending(
            log, 'Unable to find %d movie(s) in Plex, list has been saved to: %s',
            self.current.account, 'movies', self.current.pending['movies'].keys
        )
