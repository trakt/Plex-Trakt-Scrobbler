from trakt.mapper.core.base import Mapper


class SearchMapper(Mapper):
    @classmethod
    def process(cls, item, media=None, **kwargs):
        if media is None:
            # Retrieve `media` from `item`
            media = item.get('type')

        if not media:
            return ValueError()

        # Find function for `media`
        func = getattr(cls, media, None)

        if not func:
            raise ValueError('Unknown media type: %r', media)

        # Map item
        return func(item, **kwargs)

    @classmethod
    def movie(cls, item, **kwargs):
        if 'movie' in item:
            i_movie = item['movie']
        else:
            i_movie = item

        # Retrieve item keys
        pk, keys = cls.get_ids('movie', i_movie)

        if pk is None:
            return None

        # Create object
        movie = cls.create('movie', i_movie, keys, **kwargs)

        if 'movie' in item:
            movie.update(item)

        return movie

    @classmethod
    def list(cls, item, **kwargs):
        return None

    @classmethod
    def officiallist(cls, item, **kwargs):
        return None

    @classmethod
    def show(cls, item, **kwargs):
        if 'show' in item:
            i_show = item['show']
        else:
            i_show = item

        # Retrieve item keys
        pk, keys = cls.get_ids('show', i_show)

        if pk is None:
            return None

        # Create object
        show = cls.create('show', i_show, keys, **kwargs)

        # Update with root info
        if 'show' in item:
            show.update(item)

        return show

    @classmethod
    def episodes(cls, items, **kwargs):
        return [cls.episode(item, **kwargs) for item in items]

    @classmethod
    def episode(cls, item, **kwargs):
        if 'episode' in item:
            i_episode = item['episode']
        else:
            i_episode = item

        # Retrieve item keys
        pk, keys = cls.get_ids('episode', i_episode)

        if pk is None:
            return None

        # Create object
        episode = cls.create('episode', i_episode, keys, **kwargs)

        if 'show' in item:
            episode.show = cls.show(item['show'])

        if 'season' in item:
            episode.season = cls.season(item['season'])

        # Update with root info
        if 'episode' in item:
            episode.update(item)

        return episode
