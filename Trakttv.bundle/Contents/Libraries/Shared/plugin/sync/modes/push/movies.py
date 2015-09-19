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
    @elapsed.clock
    def run(self):
        # Retrieve movie sections
        p_sections, p_sections_map = self.sections('movie')

        # Fetch movies with account settings
        p_items = self.plex.library.movies.mapped(
            p_sections, [
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

        # Task started
        pending_movies = self.trakt.movies.copy()
        unsupported_movies = {}

        # Iterate over plex movies
        for rating_key, p_guid, p_item in p_items:
            if not p_guid or p_guid.agent not in GUID_AGENTS:
                mark_unsupported(unsupported_movies, rating_key, p_guid, p_item)
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
            if pk and pk in pending_movies:
                pending_movies.remove(pk)

            # Task checkpoint
            self.checkpoint()

        # Iterate over trakt movies (that aren't in plex)
        for pk in list(pending_movies):
            triggered = False

            # Iterate over data handlers
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
            pending_movies.remove(pk)

        # Log details
        log_unsupported(log, 'Found %d unsupported movie(s)\n%s', unsupported_movies)
        self.log_pending('Unable to process %d movie(s)\n%s', pending_movies)
