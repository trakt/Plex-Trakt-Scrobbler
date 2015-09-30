from trakt.mapper.core.base import Mapper

import logging

log = logging.getLogger(__name__)


class SyncMapper(Mapper):
    @classmethod
    def process(cls, client, store, items, media, **kwargs):
        if not media:
            return ValueError()

        func = getattr(cls, media)

        if not func:
            raise ValueError('Unknown media type: %r', media)

        return func(client, store, items, **kwargs)

    #
    # Movie
    #

    @classmethod
    def movies(cls, client, store, items, **kwargs):
        return cls.map_items(client, store, items, cls.movie, **kwargs)

    @classmethod
    def movie(cls, client, store, item, **kwargs):
        movie = cls.map_item(client, store, item, 'movie', **kwargs)

        # Update with root info
        if 'movie' in item:
            movie._update(item)

        return movie

    #
    # Show
    #

    @classmethod
    def shows(cls, client, store, items, **kwargs):
        return cls.map_items(client, store, items, cls.show, **kwargs)

    @classmethod
    def show(cls, client, store, item, **kwargs):
        show = cls.map_item(client, store, item, 'show', **kwargs)

        # Update with root info
        if 'show' in item:
            show._update(item)

        # Process any episodes in the item
        for i_season in item.get('seasons', []):
            season_num = i_season.get('number')

            season = cls.show_season(client, show, season_num, **kwargs)

            for i_episode in i_season.get('episodes', []):
                episode_num = i_episode.get('number')

                cls.show_episode(client, season, episode_num, i_episode, **kwargs)

        return show

    @classmethod
    def show_season(cls, client, show, season_num, item=None, **kwargs):
        season = cls.map_item(client, show.seasons, item, 'season', key=season_num, parent=show, **kwargs)
        season.show = show

        # Update with root info
        if item and 'season' in item:
            season._update(item)

        return season

    @classmethod
    def show_episode(cls, client, season, episode_num, item=None, **kwargs):
        episode = cls.map_item(client, season.episodes, item, 'episode', key=episode_num, parent=season, **kwargs)
        episode.show = season.show
        episode.season = season

        # Update with root info
        if item and 'episode' in item:
            episode._update(item)

        return episode

    #
    # Season
    #

    @classmethod
    def seasons(cls, client, store, items, **kwargs):
        return cls.map_items(client, store, items, cls.season, **kwargs)

    @classmethod
    def season(cls, client, store, item, **kwargs):
        i_season = item.get('season', {})

        season_num = i_season.get('number')

        # Build `show`
        show = cls.show(client, store, item['show'])

        if show is None:
            # Unable to create show
            return None

        # Build `season`
        season = cls.show_season(client, show, season_num, item, **kwargs)

        return season

    #
    # Episode
    #

    @classmethod
    def episodes(cls, client, store, items, **kwargs):
        return cls.map_items(client, store, items, cls.episode, **kwargs)

    @classmethod
    def episode(cls, client, store, item, **kwargs):
        i_episode = item.get('episode', {})

        season_num = i_episode.get('season')
        episode_num = i_episode.get('number')

        # Build `show`
        show = cls.show(client, store, item['show'])

        if show is None:
            # Unable to create show
            return None

        # Build `season`
        season = cls.show_season(client, show, season_num, **kwargs)

        # Build `episode`
        episode = cls.show_episode(client, season, episode_num, item, **kwargs)

        return episode

    #
    # Helpers
    #

    @classmethod
    def map_items(cls, client, store, items, func, **kwargs):
        if store is None:
            store = {}

        for item in items:
            result = func(client, store, item, **kwargs)

            if result is None:
                log.warn('Unable to map item: %s', item)

        return store

    @classmethod
    def map_item(cls, client, store, item, media, key=None, parent=None, **kwargs):
        if item and media in item:
            i_data = item[media]
        else:
            i_data = item

        pk, keys = cls.get_ids(media, i_data, parent=parent)

        if key is not None:
            pk = key

            if not keys:
                keys = [pk]

        if pk is None:
            # Item has no keys
            return None

        if pk not in store:
            # Create new item
            store[pk] = cls.construct(client, media, i_data, keys, **kwargs)
        else:
            # Update existing item
            store[pk]._update(i_data, **kwargs)

        return store[pk]
