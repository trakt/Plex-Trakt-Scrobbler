from plugin.sync.core.constants import GUID_AGENTS
from plugin.sync.core.enums import SyncMedia, SyncData
from plugin.sync.modes.core.base import log_unsupported, mark_unsupported
from plugin.sync.modes.push.base import Base

from plex_database.models import MetadataItem, MediaItem
from plex_metadata import Guid
import elapsed
import logging

log = logging.getLogger(__name__)


class Movies(Base):
    def __init__(self, task):
        super(Movies, self).__init__(task)

        # Sections
        self.p_sections = None
        self.p_sections_map = None

        # Items
        self.p_count = None
        self.p_movies = None

        self.p_pending = None
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
        self.current.progress.add(self.p_count)

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

        # Reset state
        self.p_pending = self.trakt.table.movies.copy()
        self.p_unsupported = {}

    @elapsed.clock
    def run(self):
        # Process movies
        self.process_matches()
        self.process_missing()

    def process_matches(self):
        """Trigger actions for movies that have been matched in plex"""

        # Iterate over movies
        for rating_key, p_guid, p_item in self.p_movies:
            # Increment one step
            self.current.progress.step()

            # Ensure `p_guid` is available
            if not p_guid or p_guid.agent not in GUID_AGENTS:
                mark_unsupported(self.p_unsupported, rating_key, p_guid, p_item)
                continue

            key = (p_guid.agent, p_guid.sid)

            # Try retrieve `pk` for `key`
            pk = self.trakt.table.get(key)

            for data in self.get_data(SyncMedia.Movies):
                t_movie = self.trakt[(SyncMedia.Movies, data)].get(pk)

                self.execute_handlers(
                    SyncMedia.Movies, data,

                    key=rating_key,

                    p_guid=p_guid,
                    p_item=p_item,

                    t_item=t_movie
                )

            # Remove movie from `pending` set
            if pk and pk in self.p_pending:
                self.p_pending.remove(pk)

            # Task checkpoint
            self.checkpoint()

        # Report unsupported movies (unsupported guid)
        log_unsupported(log, 'Found %d unsupported movie(s)\n%s', self.p_unsupported)

    def process_missing(self):
        """Trigger actions for movies that are in trakt, but was unable to be found in plex"""

        # Increment progress steps
        self.current.progress.add(len(self.p_pending))

        # Iterate over movies
        for pk in list(self.p_pending):
            # Increment one step
            self.current.progress.step()

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
                    SyncMedia.Movies, data,

                    key=None,

                    p_guid=Guid(*pk),
                    p_item=None,

                    t_item=t_movie
                )

                # Mark triggered
                triggered = True

            # Check if action was triggered
            if not triggered:
                continue

            # Remove movie from `pending` set
            self.p_pending.remove(pk)

        # Report pending movies (no actions triggered)
        self.log_pending('Unable to process %d movie(s)\n%s', self.p_pending)
