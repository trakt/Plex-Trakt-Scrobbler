from trakt.objects import Episode, Movie, Show, Season

IDENTIFIERS = {
    'movies': [
        'imdb',
        'tmdb'
    ],
    'shows': [
        'tvdb',
        'imdb',
        'tvrage'
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
        pk, keys = self.get_ids(media, item['movie'])

        if pk is None:
            # Item has no keys
            return None

        if pk not in self.store:
            # Create new item
            self.store[pk] = self.create(media, item, keys, **kwargs)
        else:
            # Update existing item
            self.store[pk].update(item, **kwargs)

        return self.store[pk]

    def show(self, media, item, **kwargs):
        if 'show' in item:
            i_show = item['show']
        else:
            i_show = item

        pk, keys = self.get_ids(media, i_show)

        if pk is None:
            # Item has no keys
            return None

        if pk not in self.store:
            # Create new item
            self.store[pk] = self.create(media, i_show, keys, **kwargs)
        else:
            # Update existing item
            self.store[pk].update(i_show, **kwargs)

        show = self.store[pk]

        # Update with root info
        if 'show' in item:
            show.update(item)

        # Process any episodes in the item
        for i_season in item.get('seasons', []):
            season_num = i_season.get('number')

            season = self.show_season(show, season_num, **kwargs)

            for i_episode in i_season.get('episodes', []):
                episode_num = i_episode.get('number')

                self.show_episode(season, episode_num, i_episode, **kwargs)

        return show

    @staticmethod
    def show_season(show, pk, item=None, **kwargs):
        if pk not in show.seasons:
            show.seasons[pk] = Season.create(pk, item, **kwargs)
        else:
            show.seasons[pk].update(item, **kwargs)

        return show.seasons[pk]

    @staticmethod
    def show_episode(season, pk, item=None, **kwargs):
        if pk not in season.episodes:
            season.episodes[pk] = Episode.create(pk, item, **kwargs)
        else:
            season.episodes[pk].update(item, **kwargs)

        if item and 'episode' in item:
            season.episodes[pk].update(item['episode'])

        return season.episodes[pk]

    def episode(self, media, item, **kwargs):
        i_episode = item.get('episode', {})

        season_num = i_episode.get('season')
        episode_num = i_episode.get('number')

        show = self.show('shows', item['show'])
        season = self.show_season(show, season_num, **kwargs)

        episode = self.show_episode(season, episode_num, item, **kwargs)

        return episode

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

        if media == 'episodes':
            keys.append((item.get('season'), item.get('number')))

        if not len(keys):
            return None, []

        return keys[0], keys

    @classmethod
    def create(cls, media, item, keys=None, **kwargs):
        if keys is None:
            pk, keys = cls.get_ids(media, item)
        else:
            pk = keys[0]

        if media == 'shows':
            return Show.create(keys, item, **kwargs)

        if media == 'movies':
            return Movie.create(keys, item, **kwargs)

        if media == 'episodes':
            return Episode.create(pk, **kwargs)

        raise ValueError('Unknown media type provided')
