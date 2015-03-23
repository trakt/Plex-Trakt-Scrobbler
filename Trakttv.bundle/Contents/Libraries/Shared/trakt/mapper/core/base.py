from trakt.objects import Show, Episode, Season
from trakt.objects import Movie

IDENTIFIERS = {
    'movie': [
        'imdb',
        'tmdb',

        'slug',
        'trakt'
    ],
    'show': [
        'tvdb',
        'tmdb',
        'imdb',
        'tvrage',

        'slug',
        'trakt'
    ],
    'season': [
        'tvdb',
        'tmdb',

        'trakt'
    ],
    'episode': [
        'tvdb',
        'tmdb',
        'imdb',
        'tvrage',

        'trakt'
    ]
}


class Mapper(object):
    @staticmethod
    def get_ids(media, item):
        if not item:
            return None, []

        ids = item.get('ids', {})

        keys = []
        for key in IDENTIFIERS.get(media, []):
            value = ids.get(key)

            if not value:
                continue

            keys.append((key, str(value)))

        if media == 'season':
            keys.insert(0, item.get('number'))

        if media == 'episode':
            keys.insert(0, (item.get('season'), item.get('number')))

        if not len(keys):
            return None, []

        return keys[0], keys

    @classmethod
    def create(cls, media, item, keys=None, **kwargs):
        if keys is None:
            _, keys = cls.get_ids(media, item)

        if media == 'movie':
            return Movie.create(keys, item, **kwargs)

        if media == 'show':
            return Show.create(keys, item, **kwargs)

        if media == 'season':
            return Season.create(keys, item, **kwargs)

        if media == 'episode':
            return Episode.create(keys, item, **kwargs)

        raise ValueError('Unknown media type provided')
