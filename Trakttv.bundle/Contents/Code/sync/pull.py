from core.helpers import plural, all
from core.logger import Logger
from plex.plex_media_server import PlexMediaServer
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

        return True

    def run_watched(self, p_episode, t_episode):
        return self.watch(p_episode, t_episode)

    def run_ratings(self, p_episode, t_episode):
        return self.rate(p_episode, t_episode)


class Show(Base):
    key = 'show'
    children = [Episode]

    def run(self, section=None):
        self.check_stopping()

        enabled_funcs = self.get_enabled_functions()

        p_shows = self.plex.library('show')

        # Fetch library, and only get ratings and collection if enabled
        t_shows, t_shows_table = self.trakt.merged('shows', ratings='ratings' in enabled_funcs, collected=True)

        if t_shows is None:
            log.warn('Unable to construct merged library from trakt')
            return False

        self.start(len(t_shows_table))

        for x, (key, t_show) in enumerate(t_shows_table.items()):
            self.check_stopping()

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

            self.progress(x + 1)

        self.finish()
        self.check_stopping()

        # Trigger plex missing show/episode discovery
        self.discover_missing(t_shows)

        log.info('Finished pulling shows from trakt')
        return True

    def discover_missing(self, t_shows):
        # Ensure collection cleaning is enabled
        if not Prefs['sync_clean_collection']:
            return

        log.info('Searching for shows/episodes that are missing from plex')

        # Find collected shows that are missing from Plex
        t_collection_missing = self.get_missing(t_shows, is_collected=False)

        # Discover entire shows missing
        num_shows = 0
        for key, t_show in t_collection_missing.items():
            # Ignore show if there are no collected episodes on trakt
            if all([not e.is_collected for (_, e) in t_show.episodes.items()]):
                continue

            self.store('missing.shows', t_show.to_info())
            num_shows = num_shows + 1

        # Discover episodes missing
        num_episodes = 0
        for key, t_show in t_shows.items():
            if t_show.pk in t_collection_missing:
                continue

            t_episodes_missing = self.get_missing(t_show.episodes)

            if not t_episodes_missing:
                continue

            self.store_episodes(
                'missing.episodes', t_show.to_info(),
                episodes=[x.to_info() for x in t_episodes_missing.itervalues()]
            )

            num_episodes = num_episodes + len(t_episodes_missing)

        log.info(
            'Found %s show%s and %s episode%s missing from plex',
            num_shows, plural(num_shows),
            num_episodes, plural(num_episodes)
        )

    def run_ratings(self, p_shows, t_show):
        return self.rate(p_shows, t_show)


class Movie(Base):
    key = 'movie'

    def run(self, section=None):
        self.check_stopping()

        enabled_funcs = self.get_enabled_functions()

        p_movies = self.plex.library('movie')

        # Fetch library, and only get ratings and collection if enabled
        t_movies, t_movies_table = self.trakt.merged('movies', ratings='ratings' in enabled_funcs, collected=True)

        if t_movies is None:
            log.warn('Unable to construct merged library from trakt')
            return False

        self.start(len(t_movies_table))

        for x, (key, t_movie) in enumerate(t_movies_table.items()):
            self.check_stopping()
            self.progress(x + 1)

            if key is None or key not in p_movies:
                continue

            log.debug('Processing "%s" [%s]', t_movie.title, key)
            t_movie.is_local = True

            # TODO check result
            self.trigger(enabled_funcs, p_movies=p_movies[key], t_movie=t_movie)

        self.finish()
        self.check_stopping()

        # Trigger plex missing movie discovery
        self.discover_missing(t_movies)

        log.info('Finished pulling movies from trakt')
        return True

    def discover_missing(self, t_movies):
        # Ensure collection cleaning is enabled
        if not Prefs['sync_clean_collection']:
            return

        log.info('Searching for movies that are missing from plex')

        # Find collected movies that are missing from Plex
        t_collection_missing = self.get_missing(t_movies)

        num_movies = 0
        for key, t_movie in t_collection_missing.items():
            log.debug('Unable to find "%s" [%s] in library', t_movie.title, key)
            self.store('missing.movies', t_movie.to_info())
            num_movies = num_movies + 1

        log.info('Found %s movie%s missing from plex', num_movies, plural(num_movies))

    def run_watched(self, p_movies, t_movie):
        return self.watch(p_movies, t_movie)

    def run_ratings(self, p_movies, t_movie):
        return self.rate(p_movies, t_movie)


class Pull(Base):
    key = 'pull'
    title = 'Pull'
    children = [Show, Movie]
    threaded = True
