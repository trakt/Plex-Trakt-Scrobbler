from plugin.core.helpers.variable import try_convert

from plex_metadata import Guid
import logging

log = logging.getLogger(__name__)


class Identifier(object):
    @classmethod
    def get_ids(cls, guid, strict=True):
        ids = {}

        if not guid:
            return ids

        if type(guid) is str:
            # Parse raw guid
            guid = Guid.parse(guid)

        if guid.agent == 'imdb':
            ids['imdb'] = guid.sid
        elif guid.agent == 'tmdb':
            ids['tmdb'] = try_convert(guid.sid, int)
        elif guid.agent == 'tvdb':
            ids['tvdb'] = try_convert(guid.sid, int)
        elif not strict:
            log.info('Unknown Guid agent: "%s"', guid.agent)
        else:
            log.info('Unknown Guid agent: "%s" [strict]', guid.agent)
            return None

        return ids
