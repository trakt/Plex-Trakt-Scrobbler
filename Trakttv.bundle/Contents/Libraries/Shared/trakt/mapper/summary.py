from trakt.mapper.core.base import Mapper


class SummaryMapper(Mapper):
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

        return movie

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
    def seasons(cls, items, **kwargs):
        return [cls.season(item, **kwargs) for item in items]

    @classmethod
    def season(cls, item, **kwargs):
        if 'season' in item:
            i_season = item['season']
        else:
            i_season = item

        # Retrieve item keys
        pk, keys = cls.get_ids('season', i_season)

        if pk is None:
            return None

        # Create object
        season = cls.create('season', i_season, keys, **kwargs)

        return season

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

        return episode
