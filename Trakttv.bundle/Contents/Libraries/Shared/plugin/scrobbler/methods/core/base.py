from plugin.core.helpers.variable import merge
from plugin.core.identifier import Identifier

from plex.objects.library.metadata.episode import Episode
from plex.objects.library.metadata.movie import Movie
from plex_metadata import Metadata, Guid


class Base(object):
    @classmethod
    def build_request(cls, session):
        metadata = Metadata.get(session.rating_key)
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
