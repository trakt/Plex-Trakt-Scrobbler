from core.helpers import try_convert

from plex.objects.library.metadata.episode import Episode
from plex.objects.library.metadata.movie import Movie
from plex.objects.library.metadata.show import Show
from plex_metadata import Guid, Matcher
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
    def to_trakt(cls, key, p_item, guid=None, year=None):
        data = {}

        if type(p_item) is Episode:
            data['number'] = key

        if type(p_item) is Movie or type(p_item) is Show:
            p_root = cls.get_root(p_item)

            data['title'] = p_root.title

            if year:
                data['year'] = year
            elif p_root.year is not None:
                data['year'] = p_root.year
            elif p_item.year is not None:
                data['year'] = p_item.year

            # Set identifier on movie/show objects
            ActionHelper.set_identifier(data, guid or p_root.guid)

        return data


class TraktHelper(object):
    @classmethod
    def episodes(cls, episodes):
        result = []

        for episode in episodes:
            _, episodes = Matcher.process(episode)

            for episode_num in episodes:
                result.append({
                    'number': episode_num
                })

        return result


class ActionHelper(object):
    plex = PlexHelper
    trakt = TraktHelper

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
