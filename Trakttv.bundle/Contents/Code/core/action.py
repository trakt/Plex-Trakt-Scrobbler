from core.helpers import try_convert

from plex.objects.library.metadata.episode import Episode
from plex_metadata import Guid
import logging

log = logging.getLogger(__name__)


class PlexHelper(object):
    @staticmethod
    def get_root(p_item):
        if isinstance(p_item, Episode):
            return p_item.show

        return p_item

    # TODO [trakt-v2] how are title/year identifiers defined?
    @classmethod
    def to_trakt(cls, key, p_item, include_identifier=True, guid=None, year=None):
        data = {}

        if include_identifier:
            p_root = cls.get_root(p_item)

            data['title'] = p_root.title

            if year:
                data['year'] = year
            elif p_root.year is not None:
                data['year'] = p_root.year
            elif p_item.year is not None:
                data['year'] = p_item.year

            ActionHelper.set_identifier(data, guid or p_root.guid)

        return data


class ActionHelper(object):
    plex = PlexHelper

    @classmethod
    def set_identifier(cls, data, guid):
        if not guid:
            return

        if type(guid) is str:
            # Parse raw guid
            guid = Guid.parse(guid)

        if 'ids' not in data:
            data['ids'] = {}

        ids = data['ids']

        if guid.agent == 'imdb':
            ids['imdb'] = guid.sid
        elif guid.agent == 'themoviedb':
            ids['tmdb'] = try_convert(guid.sid, int)
        elif guid.agent == 'thetvdb':
            ids['tvdb'] = try_convert(guid.sid, int)
        else:
            log.warn('Unknown GUID agent "%s"', guid.agent)

        return data
