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

        return data

    @classmethod
    def get_trakt_data(cls, key, item):
        data = {
            'title': item.title,
            'year': item.year
        }

        return cls.add_identifier(data, key)



class Episode(Base):
    key = 'episode'
    auto_run = False


class Show(Base):
    key = 'show'
    children = [Episode]


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
        # Filter by rated plex movies
        p_movies = [x for x in p_movies if x.user_rating is not None]

        # Ignore if none of the plex items have a rating attached
        if not p_movies:
            return True

        # TODO should this be handled differently when there are multiple ratings?
        p_movie = p_movies[0]

        # Ignore if rating is already on trakt
        if t_movie and t_movie.rating_advanced == p_movie.user_rating:
            return True

        data = self.get_trakt_data(key, p_movie)

        data.update({
            'rating': p_movie.user_rating
        })

        self.store('ratings', data)

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
