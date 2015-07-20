from trakt.objects import Movie, Show, Episode, Season, CustomList

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
    ],
    'custom_list': [
        'trakt',
        'slug'
    ]
}


class Mapper(object):
    @staticmethod
    def get_ids(media, item, parent=None):
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
            keys.insert(0, (
                item.get('season') or parent.pk,
                item.get('number')
            ))

        if not len(keys):
            return None, []

        return keys[0], keys

    @classmethod
    def construct(cls, client, media, item, keys=None, **kwargs):
        if keys is None:
            _, keys = cls.get_ids(media, item)

        if media == 'movie':
            return Movie._construct(client, keys, item, **kwargs)

        if media == 'show':
            return Show._construct(client, keys, item, **kwargs)

        if media == 'season':
            return Season._construct(client, keys, item, **kwargs)

        if media == 'episode':
            return Episode._construct(client, keys, item, **kwargs)

        if media == 'custom_list':
            return CustomList._construct(client, keys, item, **kwargs)

        raise ValueError('Unknown media type provided')
