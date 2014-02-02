from core.logger import Logger
from plex.media_server_new import PlexMediaServer
from sync.sync_base import SyncBase
from datetime import datetime


log = Logger('sync.pull')


class Base(SyncBase):
    task = 'pull'

    @staticmethod
    def get_missing(t_items, is_collected=True):
        return dict([
            (t_item.pk, t_item) for t_item in t_items.itervalues()
            if (not is_collected or t_item.is_collected) and not t_item.is_local
        ])

    def watch(self, p_items, t_item):
        if type(p_items) is not list:
            p_items = [p_items]

        if not t_item.is_watched:
            return True

        for p_item in p_items:
            # Ignore already seen movies
            if p_item.seen:
                continue

            PlexMediaServer.scrobble(p_item.rating_key)

        return True

    def rate(self, p_items, t_item):
        if type(p_items) is not list:
            p_items = [p_items]

        if t_item.rating_advanced is None:
            return True

        t_rating = t_item.rating_advanced

        for p_item in p_items:
            # Ignore already rated episodes
            if p_item.user_rating == t_rating:
                continue

            if p_item.user_rating is None or self.rate_conflict(p_item, t_item):
                PlexMediaServer.rate(p_item.rating_key, t_rating)

        return True

    def rate_conflict(self, p_item, t_item):
        status = self.get_status()

        # First run, overwrite with trakt rating
        if status.last_success is None:
            return True

        t_timestamp = datetime.utcfromtimestamp(t_item.rating_timestamp)

        # If trakt rating was created after the last sync, update plex rating
        if t_timestamp > status.last_success:
            return True

        log.info(
            'Conflict when updating rating for item %s (plex: %s, trakt: %s), trakt rating will be changed on next push.',
            p_item.rating_key, p_item.user_rating, t_item.rating_advanced
        )

        return False


class Episode(Base):
    key = 'episode'
    auto_run = False

    def run(self, p_episodes, t_episodes):
        enabled_funcs = self.get_enabled_functions()

        for key, t_episode in t_episodes.items():
            if key is None or key not in p_episodes:
                continue

            t_episode.is_local = True

            # TODO check result
            self.trigger(enabled_funcs, p_episode=p_episodes[key], t_episode=t_episode)

        # Find collected episodes that are missing from Plex
        t_collection_missing = self.get_missing(t_episodes)

        if t_collection_missing:
            log.debug('%s episodes missing', len(t_collection_missing))
            log.debug('t_collection_missing: %s', t_collection_missing)

        return True

    def run_watched(self, p_episode, t_episode):
        return self.watch(p_episode, t_episode)

    def run_ratings(self, p_episode, t_episode):
        return self.rate(p_episode, t_episode)


class Show(Base):
    key = 'show'
    children = [Episode]

    def run(self, section=None):
        enabled_funcs = self.get_enabled_functions()

        p_shows = self.plex.library('show')

        # Fetch library, and only get ratings and collection if enabled
        t_shows = self.trakt.merged('shows', ratings='ratings' in enabled_funcs, collected=True)

        if t_shows is None:
            log.warn('Unable to construct merged library from trakt')
            return False

        for key, t_show in t_shows.items():
            if key is None or key not in p_shows or not t_show.episodes:
                continue

            log.debug('Processing "%s" [%s]', t_show.title, key)

            t_show.is_local = True

            # Trigger show functions
            self.trigger(enabled_funcs, p_shows=p_shows[key], t_show=t_show)

            # Run through each matched show and run episode functions
            for p_show in p_shows[key]:
                self.child('episode').run(
                    p_episodes=self.plex.episodes(p_show.rating_key, p_show),
                    t_episodes=t_show.episodes
                )

        # Find collected episodes that are missing from Plex
        # TODO only run if collection cleaning is enabled
        t_collection_missing = self.get_missing(t_shows, is_collected=False)

        # Discover missing episodes when the entire show is missing
        for key, t_show in t_collection_missing.items():
            log.debug('Unable to find "%s" [%s] in library', t_show.title, key)

            # Discover missing episodes
            self.child('episode').run(
                p_episodes={},
                t_episodes=t_show.episodes
            )

        # TODO construct list of missing episodes, 'un-library' them on trakt

        log.info('Finished pulling shows from trakt')
        return True

    def run_ratings(self, p_shows, t_show):
        return self.rate(p_shows, t_show)


class Movie(Base):
    key = 'movie'

    def run(self, section=None):
        enabled_funcs = self.get_enabled_functions()

        p_movies = self.plex.library('movie')

        # Fetch library, and only get ratings and collection if enabled
        t_movies = self.trakt.merged('movies', ratings='ratings' in enabled_funcs, collected=True)

        if t_movies is None:
            log.warn('Unable to construct merged library from trakt')
            return False

        for key, t_movie in t_movies.items():
            if key is None or key not in p_movies:
                continue

            log.debug('Processing "%s" [%s]', t_movie.title, key)
            t_movie.is_local = True

            # TODO check result
            self.trigger(enabled_funcs, p_movies=p_movies[key], t_movie=t_movie)

        # Find collected movies that are missing from Plex
        # TODO only run if collection cleaning is enabled
        t_collection_missing = self.get_missing(t_movies)

        for key, t_movie in t_collection_missing.items():
            log.debug('Unable to find "%s" [%s] in library', t_movie.title, key)
            self.store('missing', t_movie.to_info())

        log.debug('missing: %s', self.artifacts.get('missing'))

        # TODO 'un-library' missing movies on trakt

        log.info('Finished pulling movies from trakt')
        return True

    def run_watched(self, p_movies, t_movie):
        return self.watch(p_movies, t_movie)

    def run_ratings(self, p_movies, t_movie):
        return self.rate(p_movies, t_movie)


class Pull(Base):
    key = 'pull'
    title = 'Pull'
    children = [Show, Movie]
    threaded = True
