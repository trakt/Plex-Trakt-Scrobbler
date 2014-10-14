import hashlib
import struct


class Packer(object):
    key_code = {
        'thetvdb': 1,
        'imdb'   : 2,
        'tvrage' : 3
    }

    @classmethod
    def pack(cls, obj):
        p_name = obj.__class__.__name__.lower()
        p_method = getattr(cls, 'pack_' + p_name, None)

        if p_method:
            return p_method(obj)

        raise Exception("Unknown object specified - name: %r" % p_name)

    @classmethod
    def pack_movie(cls, movie):
        result = {
            '_': 'show',

            'k': [
                (cls.key_code.get(key), value)
                for (key, value) in movie.keys
            ],

            'c': movie.is_collected,
            'r': struct.pack('If', movie.rating.timestamp, movie.rating.advanced) if movie.rating else None,
            't': movie.title,
            'w': movie.is_watched,
            'y': struct.pack('H', movie.year),
        }

        # TODO check performance of this
        # Generate item hash
        m = hashlib.md5()
        m.update(repr(result))

        result['@'] = m.hexdigest()

        return result

    @classmethod
    def pack_show(cls, show):
        result = {
            '_': 'show',

            'k': [
                (cls.key_code.get(key), value)
                for (key, value) in show.keys
            ],

            'r': struct.pack('If', show.rating.timestamp, show.rating.advanced) if show.rating else None,
            't': show.title,
            'y': struct.pack('H', show.year),

            'z': {
                'c': [
                    struct.pack('HH', se, ep)
                    for (se, ep), episode in show.episodes.items()
                    if episode.is_collected
                ],
                'r': [
                    struct.pack('HHIf', se, ep, episode.rating.timestamp, episode.rating.advanced)
                    for (se, ep), episode in show.episodes.items()
                    if episode.rating is not None
                ],
                'w': [
                    struct.pack('HH', se, ep)
                    for (se, ep), episode in show.episodes.items()
                    if episode.is_watched
                ]
            }
        }

        # TODO check performance of this
        # Generate item hash
        m = hashlib.md5()
        m.update(repr(result))

        result['@'] = m.hexdigest()

        return result
