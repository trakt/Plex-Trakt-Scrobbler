from plugin.core.filters import Filters
from plugin.core.helpers.variable import merge
from plugin.core.identifier import Identifier
from plugin.managers.session.base import UpdateSession

from plex.objects.library.metadata.episode import Episode
from plex.objects.library.metadata.movie import Movie
from plex_metadata import Metadata, Guid
import logging

log = logging.getLogger(__name__)


class Base(object):
    name = None

    @classmethod
    def build_request(cls, session, rating_key=None, view_offset=None):
        # Retrieve metadata for session
        if rating_key is None:
            rating_key = session.rating_key

        # Retrieve metadata
        metadata = Metadata.get(rating_key)

        # Queue a flush for the metadata cache
        Metadata.cache.flush_queue()

        # Validate metadata
        if not metadata:
            log.warn('Unable to retrieve metadata for rating_key %r', rating_key)
            return None

        if metadata.type not in ['movie', 'episode']:
            log.info('Ignoring session with type %r for rating_key %r', metadata.type, rating_key)
            return None

        # Apply library/section filter
        if not Filters.is_valid_metadata_section(metadata):
            return None

        # Parse guid
        guid = Guid.parse(metadata.guid)

        # Build request from guid/metadata
        if type(metadata) is Movie:
            result = cls.build_movie(metadata, guid)
        elif type(metadata) is Episode:
            result = cls.build_episode(metadata, guid)
        else:
            return None

        if not result:
            return None

        # Retrieve media progress
        if view_offset is not None:
            # Calculate progress from `view_offset` parameter
            progress = UpdateSession.get_progress(metadata.duration, view_offset)
        else:
            # Use session progress
            progress = session.progress

        # Merge progress into request
        return merge(result, {
            'progress': progress
        })

    @staticmethod
    def build_episode(episode, guid):
        ids = Identifier.get_ids(guid, strict=False)

        if not ids:
            return None

        return {
            'show': {
                'title': episode.show.title,
                'year': episode.year,

                'ids': ids
            },
            'episode': {
                'title': episode.title,

                'season': episode.season.index,
                'number': episode.index
            }
        }

    @staticmethod
    def build_movie(movie, guid):
        ids = Identifier.get_ids(guid, strict=False)

        if not ids:
            return None

        return {
            'movie': {
                'title': movie.title,
                'year': movie.year,

                'ids': ids
            }
        }

    @staticmethod
    def session_jumped(session, view_offset):
        if session.view_offset is None:
            return False

        view_delta = view_offset - session.view_offset

        jump_offset = session.duration - session.view_offset - view_delta
        jump_perc = float(view_delta) / session.duration

        if jump_perc >= 0.98 and jump_offset < 1000:
            log.info('Session jumped: %r -> %r (delta: %r, jump_offset: %r, jump_perc: %r)', session.view_offset, view_offset, view_delta, jump_offset, jump_perc)
            return True

        return False
