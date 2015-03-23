import calendar
import hashlib
import logging
import struct

log = logging.getLogger(__name__)


class Packer(object):
    agent_codes = {
        'tvdb'    : 1,
        'imdb'    : 2,
        'tvrage'  : 3,
        'tmdb'    : 4,
        'trakt'   : 5,
        'slug'    : 6
    }

    @classmethod
    def pack(cls, obj, include=None):
        p_name = obj.__class__.__name__.lower()
        p_method = getattr(cls, 'pack_' + p_name, None)

        if include is not None and type(include) is not list:
            include = [include]

        if p_method:
            return p_method(obj, include)

        raise Exception("Unknown object specified - name: %r" % p_name)

    @classmethod
    def pack_movie(cls, movie, include):
        result = {
            '_': 'show',

            'k': [
                (cls.to_agent_code(key), value)
                for (key, value) in movie.keys
            ],

            't': movie.title,
            'y': struct.pack('H', movie.year) if movie.year else None,
        }

        # Collected
        if not include or 'c' in include:
            # ['c'] = (is_collected, timestamp)
            result['c'] = struct.pack('?I', movie.is_collected, 0)

        # Ratings
        if not include or 'r' in include:
            # ['r'] = (rating, timestamp)
            result['r'] = struct.pack('fI', movie.rating.value, cls.to_unix_timestamp(movie.rating.timestamp)) if movie.rating else None

        # Watched
        if not include or 'w' in include:
            # ['w'] = (is_watched)
            result['w'] = struct.pack('?', movie.is_watched)

        # Calculate item hash
        result['@'] = cls.hash(result)

        return result

    @classmethod
    def pack_show(cls, show, include):
        result = {
            '_': 'show',

            'k': [
                (cls.to_agent_code(key), value)
                for (key, value) in show.keys
            ],

            't': show.title,
            'y': struct.pack('H', show.year) if show.year else None,

            'z': {}
        }

        # Collected
        if not include or 'c' in include:
            # ['z']['c'] = (se, ep, timestamp)
            result['z']['c'] = [
                struct.pack('HHI', se, ep, 0)
                for (se, ep), episode in show.episodes()
                if episode.is_collected
            ]

        # Ratings
        if not include or 'r' in include:
            # ['r'] = (rating, timestamp)
            result['r'] = struct.pack('fI', show.rating.value, cls.to_unix_timestamp(show.rating.timestamp)) if show.rating else None

            # ['z']['r'] = (se, ep, rating, timestamp)
            result['z']['r'] = [
                struct.pack('HHfI', se, ep, episode.rating.value, cls.to_unix_timestamp(episode.rating.timestamp))
                for (se, ep), episode in show.episodes()
                if episode.rating is not None
            ]

        # Watched
        if not include or 'w' in include:
            result['z']['w'] = [
                struct.pack('HH', se, ep)
                for (se, ep), episode in show.episodes()
                if episode.is_watched
            ]

        # Calculate item hash
        result['@'] = cls.hash(result)

        return result

    @classmethod
    def to_agent_code(cls, key):
        result = cls.agent_codes.get(key)

        if result is None:
            log.warn('Unable to find key code for "%s"', key)

        return result

    @staticmethod
    def hash(item):
        # TODO check performance of this
        m = hashlib.md5()
        m.update(repr(item))

        return m.hexdigest()

    @staticmethod
    def to_unix_timestamp(dt):
        return calendar.timegm(dt.utctimetuple())
