from datetime import datetime
from core.logger import Logger
from plex.media_server_new import PlexMediaServer
from sync.sync_base import SyncBase


log = Logger('sync.pull')


class Base(SyncBase):
    task = 'pull'

    def rate(self, p_items, t_media):
        if t_media.rating_advanced is None:
            return True

        t_rating = t_media.rating_advanced

        for p_item in p_items:
            # Ignore already rated episodes
            if p_item.user_rating == t_rating:
                continue

            if p_item.user_rating is None or self.rate_conflict(p_item, t_media):
                PlexMediaServer.rate(p_item.rating_key, t_rating)

        return True

    def rate_conflict(self, p_item, t_media):
        status = self.get_status()

        # First run, overwrite with trakt rating
        if status.last_success is None:
            return True

        t_timestamp = datetime.utcfromtimestamp(t_media.rating_timestamp)

        # If trakt rating was created after the last sync, update plex rating
        if t_timestamp > status.last_success:
            return True

        log.info(
            'Conflict when updating rating for item %s (plex: %s, trakt: %s), trakt rating will be changed on next push.',
            p_item.rating_key, p_item.user_rating, t_media.rating_advanced
        )

        return False


class Episode(Base):
    key = 'episode'
    auto_run = False

    def run(self, p_episodes, t_episodes):
        enabled_funcs = self.get_enabled_functions()

        for key, t_episode in t_episodes.items():
            log.debug('Processing S%02dE%02d', *key)

            if key is None or key not in p_episodes:
                log.info('trakt item with key: %s, invalid or not in library', key)
                continue

            # TODO check result
            self.trigger(enabled_funcs, p_episode=p_episodes[key], t_episode=t_episode)

        return True

    def run_watched(self, p_episode, t_episode):
        if not t_episode.is_watched:
            return True

        # Ignore already seen episodes
        if p_episode.seen:
            return True

        PlexMediaServer.scrobble(p_episode.rating_key)

        return True

    def run_ratings(self, p_episode, t_episode):
        return self.rate([p_episode], t_episode)


class Show(Base):
    key = 'show'
    children = [Episode]

    def run(self, section=None):
        enabled_funcs = self.get_enabled_functions()

        p_shows = self.plex.library('show')

        # TODO include_ratings could be false when rating sync is not enabled
        t_shows = self.trakt.merged('shows', ratings=True)

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

            log.info('Processing "%s" [%s]', t_show.title, key)

            self.trigger(enabled_funcs, p_shows=p_shows[key], t_show=t_show, ignore_missing=True)

            for p_show in p_shows[key]:
                self.child('episode').run(
                    p_episodes=self.plex.episodes(p_show.rating_key, p_show),
                    t_episodes=t_show.episodes
                )

        log.info('Finished pulling shows from trakt')
        return True

    def run_ratings(self, p_shows, t_show):
        return self.rate(p_shows, t_show)


class Movie(Base):
    key = 'movie'

    def run(self, section=None):
        enabled_funcs = self.get_enabled_functions()

        p_movies = self.plex.library('movie')

        # TODO include_ratings could be false when rating sync is not enabled
        t_movies = self.trakt.merged('movies', ratings=True)

        if t_movies is None:
            log.warn('Unable to construct merged library from trakt')
            return False

        for key, t_movie in t_movies.items():
            if key is None or key not in p_movies:
                log.debug('trakt item with key: %s, invalid or not in library', key)
                continue

            log.debug('Processing "%s" [%s]', t_movie.title, key)

            # TODO check result
            self.trigger(enabled_funcs, p_movies=p_movies[key], t_movie=t_movie)

        log.info('Finished pulling movies from trakt')
        return True

    def run_watched(self, p_movies, t_movie):
        if not t_movie.is_watched:
            return True

        for p_movie in p_movies:
            # Ignore already seen movies
            if p_movie.seen:
                continue

            PlexMediaServer.scrobble(p_movie.rating_key)

        return True

    def run_ratings(self, p_movies, t_movie):
        return self.rate(p_movies, t_movie)


class Pull(Base):
    key = 'pull'
    title = 'Pull'
    children = [Show, Movie]
