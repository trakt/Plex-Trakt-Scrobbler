from trakt.objects import Episode, Movie, Show

IDENTIFIERS = {
    'movies': [
        ('imdb_id', 'imdb'),
        ('tmdb_id', 'themoviedb')
    ],
    'shows': [
        ('tvdb_id', 'thetvdb'),
        ('imdb_id', 'imdb'),
        ('tvrage_id', 'tvrage')
    ]
}


class MediaMapper(object):
    def __init__(self, store):
        self.store = store

    def process(self, media, item, **kwargs):
        if media == 'movies':
            return self.movie(media, item, **kwargs)

        if media == 'shows':
            return self.show(media, item, **kwargs)

        if media == 'episodes':
            return self.episode(media, item, **kwargs)

        raise ValueError('Unknown media provided')

    def movie(self, media, item, **kwargs):
        pk, keys = self.get_keys(media, item)

        if pk not in self.store:
            self.store[pk] = self.create(media, item, keys, **kwargs)
        else:
            self.store[pk].update(item, **kwargs)

        return self.store[pk]

    def show(self, media, item, **kwargs):
        pk, keys = self.get_keys(media, item)

        if pk not in self.store:
            self.store[pk] = self.create(media, item, keys, **kwargs)
        else:
            self.store[pk].update(item, **kwargs)

        show = self.store[pk]

        # Process any episodes in the item
        for season in item.get('seasons', []):
            season_num = season.get('season')

            for episode_num in season.get('episodes', []):
                self.show_episode(show, (season_num, episode_num), **kwargs)

        return show

    @staticmethod
    def show_episode(show, pk, item=None, **kwargs):
        if pk not in show.episodes:
            show.episodes[pk] = Episode.create(pk, item, **kwargs)
        else:
            show.episodes[pk].update(item, **kwargs)

        return show.episodes[pk]

    def episode(self, media, item, **kwargs):
        show = self.show('shows', item.get('show'))

        ep = item.get('episode')
        pk = ep.get('season'), ep.get('number')

        return self.show_episode(show, pk, item, **kwargs)

    @staticmethod
    def get_keys(media, item):
        if not item:
            return None

        keys = []
        for t_key, p_key in IDENTIFIERS.get(media, []):
            keys.append((p_key, str(item.get(t_key))))

        if media == 'episodes':
            keys.append((item.get('season'), item.get('number')))

        if not len(keys):
            return None, []

        return keys[0], keys

    @classmethod
    def create(cls, media, item, keys=None, **kwargs):
        if keys is None:
            pk, keys = cls.get_keys(media, item)
        else:
            pk = keys[0]

        if media == 'shows':
            return Show.create(keys, item, **kwargs)

        if media == 'movies':
            return Movie.create(keys, item, **kwargs)

        if media == 'episodes':
            return Episode.create(pk, **kwargs)

        raise ValueError('Unknown media type provided')
