from core.helpers import try_convert

from plex_metadata import Guid


class ActionHelper(object):
    @classmethod
    def set_identifier(cls, values, guid):
        if not guid:
            return

        if type(guid) is str:
            # Parse raw guid
            guid = Guid.parse(guid)

        if guid.agent == 'imdb':
            values['imdb_id'] = guid.sid
        elif guid.agent == 'themoviedb':
            values['tmdb_id'] = try_convert(guid.sid, int)
        elif guid.agent == 'thetvdb':
            values['tvdb_id'] = try_convert(guid.sid, int)
