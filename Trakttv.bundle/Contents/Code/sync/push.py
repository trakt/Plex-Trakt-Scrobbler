from core.helpers import all
from core.logger import Logger
from sync.sync_base import SyncBase


log = Logger('sync.push')


class Base(SyncBase):
    task = 'push'

    @staticmethod
    def add_identifier(data, (service, sid)):
        if service == 'imdb':
            data['imdb_id'] = sid

        if service == 'themoviedb':
            data['tmdb_id'] = sid

        if service == 'thetvdb':
            data['tvdb_id'] = sid

        return data

    @classmethod
    def get_trakt_data(cls, key, item):
        data = {
            'title': item.title,
            'year': item.year
        }

        return cls.add_identifier(data, key)

    def rate(self, key, p_items, t_item):
        # Filter by rated plex items
        p_items = [x for x in p_items if x.user_rating is not None]

        # Ignore if none of the plex items have a rating attached
        if not p_items:
            return True

        # TODO should this be handled differently when there are multiple ratings?
        p_item = p_items[0]

        # Ignore if rating is already on trakt
        if t_item and t_item.rating_advanced == p_item.user_rating:
            return True

        data = self.get_trakt_data(key, p_item)

        data.update({
            'rating': p_item.user_rating
        })

        self.store('ratings', data)
        return True



class Episode(Base):
    key = 'episode'
    auto_run = False

    def run(self, p_episodes, t_episodes):
        log.debug('Episode.run')


class Show(Base):
    key = 'show'
    children = [Episode]

    def run(self, section=None):
        enabled_funcs = self.get_enabled_functions()

        p_shows = self.plex.library('show')

        # TODO include_ratings could be false when rating sync is not enabled
        t_shows = self.trakt.merged('shows', ratings=True, collected=True)

        if t_shows is None:
            log.warn('Unable to construct merged library from trakt')
            return False

        for key, p_show in p_shows.items():
            t_show = t_shows.get(key)

            log.debug('Processing "%s" [%s]', p_show[0].title if p_show else None, key)

            # TODO check result
            self.trigger(enabled_funcs, key=key, p_shows=p_show, t_show=t_show, ignore_missing=True)

            for p_show in p_show:
                self.child('episode').run(
                    p_episodes=self.plex.episodes(p_show.key),
                    t_episodes=t_show.episodes
                )

        log.debug(self.artifacts)

    def run_ratings(self, key, p_shows, t_show):
        return self.rate(key, p_shows, t_show)


class Movie(Base):
    key = 'movie'

    def run(self, section=None):
        # TODO use 'section' parameter
        self.reset()

        enabled_funcs = self.get_enabled_functions()

        p_movies = self.plex.library('movie')

        # TODO include_ratings could be false when rating sync is not enabled
        t_movies = self.trakt.merged('movies', ratings=True, collected=True)

        if t_movies is None:
            log.warn('Unable to construct merged library from trakt')
            return False

        for key, p_movie in p_movies.items():
            t_movie = t_movies.get(key)

            log.debug('Processing "%s" [%s]', p_movie[0].title if p_movie else None, key)

            # TODO check result
            self.trigger(enabled_funcs, key=key, p_movies=p_movie, t_movie=t_movie)

        log.debug(self.artifacts)

    def run_watched(self, key, p_movies, t_movie):
        # Ignore if trakt movie is already watched
        if t_movie and t_movie.is_watched:
            return True

        # Ignore if none of the plex items are watched
        if all([not x.seen for x in p_movies]):
            return True

        # TODO should we instead pick the best result, instead of just the first?
        p_movie = p_movies[0]

        self.store('watched', self.get_trakt_data(key, p_movie))

    def run_ratings(self, key, p_movies, t_movie):
        return self.rate(key, p_movies, t_movie)

    def run_collected(self, key, p_movies, t_movie):
        # Ignore if trakt movie is already collected
        if t_movie and t_movie.is_collected:
            return True

        p_movie = p_movies[0]

        self.store('collected', self.get_trakt_data(key, p_movie))


class Push(Base):
    key = 'push'
    title = 'Push'
    children = [Show, Movie]
