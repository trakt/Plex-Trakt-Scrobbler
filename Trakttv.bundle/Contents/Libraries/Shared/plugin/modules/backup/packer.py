import hashlib
import struct


class Packer(object):
    key_code = {
        'thetvdb': 1,
        'imdb'   : 2,
        'tvrage' : 3
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
                (cls.key_code.get(key), value)
                for (key, value) in movie.keys
            ],

            't': movie.title,
            'y': struct.pack('H', movie.year),
        }

        # Collected
        if not include or 'c' in include:
            result['c'] = movie.is_collected

        # Ratings
        if not include or 'r' in include:
            result['r'] = struct.pack('If', movie.rating.timestamp, movie.rating.advanced) if movie.rating else None

        # Watched
        if not include or 'w' in include:
            result['w'] = movie.is_watched

        # Calculate item hash
        result['@'] = cls.hash(result)

        return result

    @classmethod
    def pack_show(cls, show, include):
        result = {
            '_': 'show',

            'k': [
                (cls.key_code.get(key), value)
                for (key, value) in show.keys
            ],

            't': show.title,
            'y': struct.pack('H', show.year),

            'z': {}
        }

        # Collected
        if not include or 'c' in include:
            result['z']['c'] = [
                struct.pack('HH', se, ep)
                for (se, ep), episode in show.episodes.items()
                if episode.is_collected
            ]

        # Ratings
        if not include or 'r' in include:
            result['r'] = struct.pack('If', show.rating.timestamp, show.rating.advanced) if show.rating else None

            result['z']['r'] = [
                struct.pack('HHIf', se, ep, episode.rating.timestamp, episode.rating.advanced)
                for (se, ep), episode in show.episodes.items()
                if episode.rating is not None
            ]

        # Watched
        if not include or 'w' in include:
            result['z']['w'] = [
                struct.pack('HH', se, ep)
                for (se, ep), episode in show.episodes.items()
                if episode.is_watched
            ]

        # Calculate item hash
        result['@'] = cls.hash(result)

        return result

    @staticmethod
    def hash(item):
        # TODO check performance of this
        m = hashlib.md5()
        m.update(repr(item))

        return m.hexdigest()
