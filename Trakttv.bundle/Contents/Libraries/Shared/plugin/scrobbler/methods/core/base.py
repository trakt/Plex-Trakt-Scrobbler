from plugin.core.helpers.variable import merge
from plugin.core.identifier import Identifier

from plex.objects.library.metadata.episode import Episode
from plex.objects.library.metadata.movie import Movie
from plex_metadata import Metadata, Guid
import logging

log = logging.getLogger(__name__)


class Base(object):
    name = None

    @classmethod
    def build_request(cls, session, rating_key=None):
        metadata = Metadata.get(rating_key or session.rating_key)
        guid = Guid.parse(metadata.guid)

        result = None

        if type(metadata) is Movie:
            result = cls.build_movie(metadata, guid)
        elif type(metadata) is Episode:
            result = cls.build_episode(metadata, guid)
        else:
            return None

        if not result:
            return None

        return merge(result, {
            'progress': session.progress
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
        view_delta = view_offset - session.view_offset

        jump_offset = session.duration - session.view_offset - view_delta
        jump_perc = float(view_delta) / session.duration

        if jump_perc >= 0.98 and jump_offset < 1000:
            log.info('Session jumped: %r -> %r (delta: %r, jump_offset: %r, jump_perc: %r)', session.view_offset, view_offset, view_delta, jump_offset, jump_perc)
            return True

        return False
