from core.logger import Logger
from plex.media_server_new import PlexMediaServer
from sync.sync_base import SyncBase


log = Logger('sync.pull')


class Base(SyncBase):
    pass


class Episode(Base):
    key = 'episode'
    auto_run = False

    def run(self, p_episodes, t_episodes):
        enabled_funcs = self.get_enabled_functions()

        for key, t_episode in t_episodes.items():
            log.info('Updating S%02dE%02d', *key)

            if key is None or key not in p_episodes:
                log.info('trakt item with key: %s, invalid or not in library', key)
                continue

            self.trigger(enabled_funcs, p_episode=p_episodes[key], t_episode=t_episode)

    def run_watched(self, p_episode, t_episode):
        if not t_episode.is_watched:
            return

        # Ignore already seen episodes
        if p_episode.seen:
            return

        PlexMediaServer.scrobble(p_episode.key)

    def run_ratings(self, p_episode, t_episode):
        if t_episode.rating_advanced is None:
            return

        rating = t_episode.rating_advanced

        # Ignore already rated episodes
        if p_episode.user_rating == rating:
            return

        PlexMediaServer.rate(p_episode.key, rating)


class Show(Base):
    key = 'show'

    children = [Episode]

    def run(self):
        enabled_funcs = self.get_enabled_functions()

        p_shows = self.plex.library('show')
        t_shows = self.trakt.merged('shows', 'watched', include_ratings=True)

        if t_shows is None:
            log.warn('Unable to construct merged library from trakt')
            return False

        for key, t_show in t_shows.items():
            if key is None or key not in p_shows:
                log.debug('trakt item with key: %s, invalid or not in library', key)
                continue

            if not t_show.episodes:
                log.warn('trakt item has no episodes, ignoring')
                continue

            log.info('Updating "%s" [%s]', t_show.title, key)

            self.trigger(enabled_funcs, p_shows=p_shows[key], t_show=t_show, ignore_missing=True)

            for p_show in p_shows[key]:
                self.child('episode').run(
                    p_episodes=self.plex.episodes(p_show.key),
                    t_episodes=t_show.episodes
                )

    def run_ratings(self, p_shows, t_show):
        if t_show.rating_advanced is None:
            return

        rating = t_show.rating_advanced

        for p_show in p_shows:
            # Ignore already rated shows
            if p_show.user_rating == rating:
                continue

            PlexMediaServer.rate(p_show.key, rating)


class Movie(Base):
    key = 'movie'

    def run(self):
        enabled_funcs = self.get_enabled_functions()

        p_movies = self.plex.library('movie')
        t_movies = self.trakt.merged('movies', 'watched', include_ratings=True)

        if t_movies is None:
            log.warn('Unable to construct merged library from trakt')
            return False

        for key, t_movie in t_movies.items():
            if key is None or key not in p_movies:
                log.debug('trakt item with key: %s, invalid or not in library', key)
                continue

            log.info('Updating "%s" [%s]', t_movie.title, key)

            self.trigger(enabled_funcs, p_movies=p_movies[key], t_movie=t_movie)

    def run_watched(self, p_movies, t_movie):
        if not t_movie.is_watched:
            return

        for p_movie in p_movies:
            # Ignore already seen movies
            if p_movie.seen:
                continue

            PlexMediaServer.scrobble(p_movie.key)

    def run_ratings(self, p_movies, t_movie):
        if t_movie.rating_advanced is None:
            return

        rating = t_movie.rating_advanced

        for p_movie in p_movies:
            # Ignore already rated movies
            if p_movie.user_rating == rating:
                continue

            PlexMediaServer.rate(p_movie.key, rating)


class Pull(Base):
    children = [Show, Movie]
