from core.helpers import all, get_pref
from core.logger import Logger
from pts.action_manager import ActionManager
from sync.sync_base import SyncBase

from plex import Plex
from plex_metadata import Library


log = Logger('sync.pull')


class Base(SyncBase):
    task = 'pull'

    @classmethod
    def get_missing(cls, t_items, is_collected=True):
        return dict([
            (t_item.pk, t_item) for t_item in t_items.itervalues()
            if (not is_collected or t_item.is_collected) and
               cls.is_missing(t_item)
        ])

    @classmethod
    def is_missing(cls, t_item):
        is_local = getattr(t_item, 'is_local', False)

        if not hasattr(t_item, 'is_collected'):
            return not is_local

        return getattr(t_item, 'is_collected') and not is_local

    def watch(self, p_items, t_item):
        if type(p_items) is not list:
            p_items = [p_items]

        if not t_item.is_watched:
            return True

        for p_item in p_items:
            # Ignore already seen movies
            if p_item.seen:
                continue

            # Scrobble item
            Plex['library'].scrobble(p_item.rating_key)

            # Mark item as added in `pts.action_manager`
            ActionManager.update_history(p_item.rating_key, 'add', 'add')

        return True


    def rate(self, p_items, t_item):
        if type(p_items) is not list:
            p_items = [p_items]

        if t_item.rating is None:
            return True

        t_rating = t_item.rating.value

        for p_item in p_items:
            # Ignore already rated episodes
            if p_item.user_rating == t_rating:
                continue

            if p_item.user_rating is None or self.rate_conflict(p_item, t_item):
                Plex['library'].rate(p_item.rating_key, t_rating)

        return True

    def rate_conflict(self, p_item, t_item):
        status = self.get_status()

        # First run, overwrite with trakt rating
        if status.last_success is None:
            return True

        resolution = get_pref('sync_ratings_conflict')

        if resolution == 'trakt':
            return True

        if resolution == 'latest':
            # If trakt rating was created after the last sync, update plex rating
            if t_item.rating.timestamp > status.last_success:
                return True

        log.info(
            'Conflict when updating rating for item %s (plex: %s, trakt: %s), trakt rating will be changed on next push.',
            p_item.rating_key, p_item.user_rating, t_item.rating.value
        )

        return False


class Episode(Base):
    key = 'episode'
    auto_run = False

    def run(self, p_episodes, t_episodes):
        if p_episodes is None:
            return False

        enabled_funcs = self.get_enabled_functions()

        for key, t_episode in t_episodes.items():
            if key is None or key not in p_episodes:
                continue

            # Mark episode as 'local'
            t_episode.is_local = True

            # TODO check result
            self.trigger(enabled_funcs, p_episode=p_episodes[key], t_episode=t_episode)

        return True

    def run_watched(self, p_episode, t_episode):
        return self.watch(p_episode, t_episode)

    def run_ratings(self, p_episode, t_episode):
        return self.rate(p_episode, t_episode)


class Season(Base):
    key = 'season'
    auto_run = False
    children = [Episode]

    def run(self, p_seasons, t_seasons):
        if p_seasons is None:
            return False

        for key, p_season in p_seasons.items():
            t_season = t_seasons.get(key)

            if t_season:
                # Mark season as 'local'
                t_season.is_local = True

            self.child('episode').run(
                p_episodes=p_season,
                t_episodes=t_season.episodes if t_season else {}
            )


class Show(Base):
    key = 'show'
    children = [Season]

    def run(self, section=None):
        self.check_stopping()

        enabled_funcs = self.get_enabled_functions()
        if not enabled_funcs:
            log.info('There are no functions enabled, skipping pull.show')
            return True

        p_shows = self.plex.library('show')
        self.save('last_library', repr(p_shows), source='plex')

        # Fetch library, and only get ratings and collection if enabled
        t_shows, t_shows_table = self.trakt.merged('shows', ratings='ratings' in enabled_funcs, collected=True)
        self.save('last_library', repr(t_shows_table), source='trakt')

        if t_shows is None:
            log.warn('Unable to construct merged library from trakt')
            return False

        self.emit('started', len(t_shows_table))

        for x, (key, t_show) in enumerate(t_shows_table.items()):
            self.check_stopping()
            self.emit('progress', x + 1)

            if key is None or key not in p_shows or not t_show.seasons:
                continue

            log.debug('Processing "%s" [%s]', t_show.title, key)

            t_show.is_local = True

            # Trigger show functions
            self.trigger(enabled_funcs, p_shows=p_shows[key], t_show=t_show)

            # Run through each matched show and run episode functions
            for p_show in p_shows[key]:
                self.child('season').run(
                    p_seasons=Library.episodes(p_show.rating_key, p_show, flat=False),
                    t_seasons=t_show.seasons if t_show else {}
                )

        self.emit('finished')
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

        for key, t_show in t_shows.items():
            # Ignore show if there are no collected episodes on trakt
            if all([not e.is_collected for (_, e) in t_show.episodes()]):
                continue

            show = t_show.to_identifier()

            if self.is_missing(t_show):
                # Entire show is missing
                log.debug('Unable to find "%s" [%s] in plex', t_show.title, key)

                self.store('missing.shows', show)
                continue

            # Create 'seasons' list
            if 'seasons' not in show:
                show['seasons'] = []

            for sk, t_season in t_show.seasons.items():
                # Ignore season if there are no collected episodes on trakt
                if all([not e.is_collected for e in t_season.episodes.values()]):
                    continue

                i_season = {'number': sk}

                if self.is_missing(t_season):
                    # Entire season is missing
                    log.debug('Unable to find S%02d of "%s" [%s] in plex', sk, t_show.title, key)

                    show['seasons'].append(i_season)
                    continue

                # Create 'episodes' list
                if 'episodes' not in i_season:
                    i_season['episodes'] = []

                for ek, t_episode in t_season.episodes.items():
                    if not self.is_missing(t_episode):
                        continue

                    log.debug('Unable to find S%02dE%02d of "%s" [%s] in plex', sk, ek, t_show.title, key)

                    # Append episode to season dict
                    i_season['episodes'].append({'number': ek})

                if not i_season['episodes']:
                    # Couldn't find any missing episodes in this season
                    continue

                # Append season to show dict
                show['seasons'].append(i_season)

            if not show['seasons']:
                # Couldn't find any missing seasons/episodes
                continue

            self.store('missing.shows', show)

        log.info('Discovered %s show(s) with missing items', len(self.retrieve('missing.shows')))

    def run_ratings(self, p_shows, t_show):
        return self.rate(p_shows, t_show)


class Movie(Base):
    key = 'movie'

    def run(self, section=None):
        self.check_stopping()

        enabled_funcs = self.get_enabled_functions()
        if not enabled_funcs:
            log.info('There are no functions enabled, skipping pull.movie')
            return True

        p_movies = self.plex.library('movie')
        self.save('last_library', repr(p_movies), source='plex')

        # Fetch library, and only get ratings and collection if enabled
        t_movies, t_movies_table = self.trakt.merged('movies', ratings='ratings' in enabled_funcs, collected=True)
        self.save('last_library', repr(t_movies_table), source='trakt')

        if t_movies is None:
            log.warn('Unable to construct merged library from trakt')
            return False

        self.emit('started', len(t_movies_table))

        for x, (key, t_movie) in enumerate(t_movies_table.items()):
            self.check_stopping()
            self.emit('progress', x + 1)

            if key is None or key not in p_movies:
                continue

            log.debug('Processing "%s" [%s]', t_movie.title, key)
            t_movie.is_local = True

            # TODO check result
            self.trigger(enabled_funcs, p_movies=p_movies[key], t_movie=t_movie)

        self.emit('finished')
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

        for key, t_movie in t_collection_missing.items():
            log.debug('Unable to find "%s" [%s] in plex', t_movie.title, key)

            self.store('missing.movies', t_movie.to_identifier())

        log.info('Discovered %s missing movie(s)', len(self.retrieve('missing.movies')))

    def run_watched(self, p_movies, t_movie):
        return self.watch(p_movies, t_movie)

    def run_ratings(self, p_movies, t_movie):
        return self.rate(p_movies, t_movie)


class Pull(Base):
    key = 'pull'
    title = 'Pull'
    children = [Show, Movie]
    threaded = True
