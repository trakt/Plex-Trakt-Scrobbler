from plugin.core.filters import Filters
from plugin.core.helpers.variable import merge
from plugin.core.identifier import Identifier
from plugin.core.logger.helpers import log_unsupported_guid
from plugin.managers.session.base import UpdateSession
from plugin.modules.core.manager import ModuleManager

from plex.objects.library.metadata.episode import Episode
from plex.objects.library.metadata.movie import Movie
from plex_metadata import Metadata, Guid
import logging

log = logging.getLogger(__name__)


class Base(object):
    name = None

    @classmethod
    def build_request(cls, session, part=None, rating_key=None, view_offset=None):
        # Retrieve metadata for session
        if part is None:
            part = session.part

        if rating_key is None:
            rating_key = session.rating_key

        # Retrieve metadata
        metadata = Metadata.get(rating_key)

        # Validate metadata
        if not metadata:
            log.warn('Unable to retrieve metadata for rating_key %r', rating_key)
            return None

        if metadata.type not in ['movie', 'episode']:
            log.info('Ignoring session with type %r for rating_key %r', metadata.type, rating_key)
            return None

        # Apply library/section filter
        if not Filters.is_valid_metadata_section(metadata):
            log.info('Ignoring session in filtered section: %r', metadata.section.title)
            return None

        # Parse guid
        guid = Guid.parse(metadata.guid, strict=True)

        if not guid or not guid.valid:
            log_unsupported_guid(log, guid)
            return None

        # Build request from guid/metadata
        if type(metadata) is Movie:
            result = cls.build_movie(metadata, guid, part)
        elif type(metadata) is Episode:
            result = cls.build_episode(metadata, guid, part)
        else:
            log.warn('Unknown metadata type: %r', type(metadata))
            return None

        if not result:
            log.info('Unable to build request for session: %r', session)
            return None

        # Retrieve media progress
        if view_offset is not None:
            # Calculate progress from `view_offset` parameter
            progress = UpdateSession.get_progress(
                metadata.duration, view_offset,
                part, session.part_count, session.part_duration
            )
        else:
            # Use session progress
            progress = session.progress

        # Merge progress into request
        return merge(result, {
            'progress': progress
        })

    @classmethod
    def build_episode(cls, episode, guid, part):
        # Retrieve show identifier
        ids = Identifier.get_ids(guid, strict=False)

        if not ids:
            # Try map episode to a supported service (with OEM)
            supported, request = ModuleManager['mapper'].request_episode(
                guid, episode,
                part=part
            )

            if not supported:
                log.info('No mappings available for service: %r', guid.service)

            return request

        # Retrieve episode number
        season_num, episodes = ModuleManager['matcher'].process(episode)

        if len(episodes) > 0 and part - 1 < len(episodes):
            episode_num = episodes[part - 1]
        elif len(episodes) > 0:
            log.warn('Part %s doesn\'t exist in episodes: %r', part, episodes)
            episode_num = episodes[0]
        else:
            log.warn('Matcher didn\'t return a valid result - season_num: %r, episodes: %r', season_num, episodes)
            episode_num = episode.index

        # Process guid episode identifier overrides
        if guid.season is not None:
            season_num = guid.season

        # Build request
        return {
            'show': {
                'title': episode.show.title,
                'year': episode.year,

                'ids': ids
            },
            'episode': {
                'title': episode.title,

                'season': season_num,
                'number': episode_num
            }
        }

    @staticmethod
    def build_movie(movie, guid, part):
        ids = Identifier.get_ids(guid, strict=False)

        if not ids:
            # Try map episode to a supported service (with OEM)
            supported, request = ModuleManager['mapper'].request_movie(
                guid, movie,
                part=part
            )

            if not supported:
                log.info('No mappings available for service: %r', guid.service)

            return request

        return {
            'movie': {
                'title': movie.title,
                'year': movie.year,

                'ids': ids
            }
        }

    @staticmethod
    def session_jumped(session, view_offset):
        if session.view_offset is None or view_offset is None:
            return False

        view_delta = view_offset - session.view_offset

        jump_offset = session.duration - session.view_offset - view_delta
        jump_perc = float(view_delta) / session.duration

        if jump_perc >= 0.98 and jump_offset < 1000:
            log.info('Session jumped: %r -> %r (delta: %r, jump_offset: %r, jump_perc: %r)', session.view_offset, view_offset, view_delta, jump_offset, jump_perc)
            return True

        return False
