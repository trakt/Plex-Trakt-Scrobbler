from core.action import ActionHelper
from core.helpers import all, plural, json_encode, merge
from core.logger import Logger
from data.watch_session import WatchSession
from sync.sync_base import SyncBase

from datetime import datetime
from plex_metadata import Library
from trakt import Trakt


log = Logger('sync.push')


class Base(SyncBase):
    task = 'push'

    def is_watching(self, p_item):
        sessions = WatchSession.all(lambda ws:
            ws.metadata and
            ws.metadata.rating_key == p_item.rating_key
        )

        for key, ws in sessions:
            if ws.active:
                return True

        return False

    def watch(self, key, p_items, t_item):
        if type(p_items) is not list:
            p_items = [p_items]

        # Ignore if trakt movie is already watched
        if t_item and t_item.is_watched:
            return True

        # Ignore if none of the plex items are watched
        if all([not x.seen for x in p_items]):
            return True

        # Ignore if we are currently watching this item
        if self.is_watching(p_items[0]):
            log.trace('[P #%s] ignored - item is currently being watched', p_items[0].rating_key)
            return True

        # TODO should we instead pick the best result, instead of just the first?
        last_viewed_at = datetime.utcfromtimestamp(p_items[0].last_viewed_at)

        self.store('watched', merge({
            'watched_at': last_viewed_at.strftime('%Y-%m-%d %H:%M:%S')
        }, ActionHelper.plex.to_trakt(key, p_items[0])))

        return True

    def rate(self, key, p_items, t_item, artifact='ratings', include_metadata=True):
        if type(p_items) is not list:
            p_items = [p_items]

        # Filter by rated plex items
        p_items = [x for x in p_items if x.user_rating is not None]

        # Ignore if none of the plex items have a rating attached
        if not p_items:
            return True if artifact else {}

        # TODO should this be handled differently when there are multiple ratings?
        p_item = p_items[0]

        # Ignore if rating is already on trakt
        if t_item and t_item.rating and t_item.rating.value == p_item.user_rating:
            return True if artifact else {}

        if include_metadata:
            data = ActionHelper.plex.to_trakt(key, p_item)
        else:
            data = {}

        data.update({
            'rating': p_item.user_rating
        })

        if artifact:
            self.store(artifact, data)
            return True

        return data

    def collect(self, key, p_items, t_item):
        if type(p_items) is not list:
            p_items = [p_items]

        # Ignore if trakt movie is already collected
        if t_item and t_item.is_collected:
            return True

        added_at = datetime.utcfromtimestamp(p_items[0].added_at)

        self.store('collected', merge({
            'collected_at': added_at.strftime('%Y-%m-%d %H:%M:%S')
        }, ActionHelper.plex.to_trakt(key, p_items[0])))

        return True

    def add(self, path, **kwargs):
        log.debug('[%s] Pushing items: %s', path, kwargs)

        response = Trakt[path].add(kwargs)

        if not response:
            log.warn('[%s] Request failed')
            return

        # Print "not_found" items (if any)
        not_found = response.get('not_found', {})

        for media, items in not_found.items():
            for item in items:
                log.warn('[%s](%s) Unable to find %r', path, media, item.get('title'))

        # Print "added" items
        added = response.get('added', {})

        if added.get('movies'):
            log.info('[%s] Added %s movies', path, added['movies'])
        elif added.get('episodes'):
            log.info('[%s] Added %s episodes', path, added['episodes'])

        # Print "existing" items
        existing = response.get('existing', {})

        if existing.get('movies'):
            log.info('[%s] Ignored %s existing movies', path, existing['movies'])
        elif existing.get('episodes'):
            log.info('[%s] Ignored %s existing episodes', path, existing['episodes'])

    def remove(self, path, **kwargs):
        raise NotImplementedError()


class Episode(Base):
    key = 'episode'
    auto_run = False

    def run(self, p_episodes, t_episodes, artifacts=None):
        self.reset(artifacts)

        if p_episodes is None:
            return False

        enabled_funcs = self.get_enabled_functions()

        for key, p_episode in p_episodes.items():
            t_episode = t_episodes.get(key)

            # TODO check result
            self.trigger(enabled_funcs, key=key, p_episode=p_episode, t_episode=t_episode)

        return True

    def run_watched(self, key, p_episode, t_episode):
        return self.watch(key, p_episode, t_episode)

    def run_ratings(self, key, p_episode, t_episode):
        return self.rate(key, p_episode, t_episode)

    def run_collected(self, key, p_episode, t_episode):
        return self.collect(key, p_episode, t_episode)


class Season(Base):
    key = 'season'
    auto_run = False
    children = [Episode]

    def run(self, p_seasons, t_seasons, artifacts=None):
        self.reset(artifacts)

        if p_seasons is None:
            return False

        for key, p_season in p_seasons.items():
            t_season = t_seasons.get(key)

            self.child('episode').run(
                p_episodes=p_season,
                t_episodes=t_season.episodes if t_season else {},
                artifacts=artifacts
            )

            self.store_episodes('collected', {'number': key})
            self.store_episodes('watched', {'number': key})
            self.store_episodes('ratings', {'number': key})


class Show(Base):
    key = 'show'
    children = [Season]

    def run(self, section=None, artifacts=None):
        self.reset(artifacts)
        self.check_stopping()

        enabled_funcs = self.get_enabled_functions()
        if not enabled_funcs:
            log.info('There are no functions enabled, skipping push.show')
            return True

        p_shows = self.plex.library('show', section)
        if not p_shows:
            # No items found, no need to continue
            return True

        # Fetch library, and only get ratings and collection if enabled
        t_shows, t_shows_table = self.trakt.merged(
            'shows',
            ratings='ratings' in enabled_funcs,
            collected='collected' in enabled_funcs
        )

        if t_shows_table is None:
            log.warn('Unable to construct merged library from trakt')
            return False

        self.emit('started', len(p_shows))

        for x, (key, p_show) in enumerate(p_shows.items()):
            self.check_stopping()
            self.emit('progress', x + 1)

            t_show = t_shows_table.get(key)

            log.debug('Processing "%s" [%s]', p_show[0].title if p_show else None, key)

            # TODO check result
            self.trigger(enabled_funcs, key=key, p_shows=p_show, t_show=t_show)

            for p_show in p_show:
                self.child('season').run(
                    p_seasons=Library.episodes(p_show.rating_key, p_show, flat=False),
                    t_seasons=t_show.seasons if t_show else {},
                    artifacts=artifacts
                )

                show = ActionHelper.plex.to_trakt(key, p_show)

                self.store_seasons('collected', show)
                self.store_seasons('watched', show)

                self.store_seasons('ratings', merge(
                    # Include show rating
                    self.rate(key, [p_show], t_show, artifact='', include_metadata=False),
                    show
                ))

        self.emit('finished')
        self.check_stopping()

        #
        # Push changes to trakt
        #
        self.add('sync/collection', shows=self.retrieve('collected'))
        self.add('sync/history', shows=self.retrieve('watched'))
        self.add('sync/ratings', shows=self.retrieve('ratings'))

        # TODO show/episode collection cleaning
        # for show in self.retrieve('missing.shows'):
        #     self.send('show/unlibrary', **show)
        #
        # for show in self.retrieve('missing.episodes'):
        #     self.send('show/episode/unlibrary', **show)

        self.save('last_artifacts', json_encode(self.artifacts))

        log.info('Finished pushing shows to trakt')
        return True


class Movie(Base):
    key = 'movie'

    def run(self, section=None, artifacts=None):
        self.reset(artifacts)
        self.check_stopping()

        enabled_funcs = self.get_enabled_functions()
        if not enabled_funcs:
            log.info('There are no functions enabled, skipping push.movie')
            return True

        p_movies = self.plex.library('movie', section)
        if not p_movies:
            # No items found, no need to continue
            return True

        # Fetch library, and only get ratings and collection if enabled
        t_movies, t_movies_table = self.trakt.merged(
            'movies',
            ratings='ratings' in enabled_funcs,
            collected='collected' in enabled_funcs
        )

        if t_movies_table is None:
            log.warn('Unable to construct merged library from trakt')
            return False

        self.emit('started', len(p_movies))

        for x, (key, p_movie) in enumerate(p_movies.items()):
            self.check_stopping()
            self.emit('progress', x + 1)

            t_movie = t_movies_table.get(key)

            log.debug('Processing "%s" [%s]', p_movie[0].title if p_movie else None, key)

            # TODO check result
            self.trigger(enabled_funcs, key=key, p_movies=p_movie, t_movie=t_movie)

        self.emit('finished')
        self.check_stopping()

        #
        # Push changes to trakt
        #
        # TODO push movie changes
        # self.send_artifact('movie/seen', 'movies', 'watched')
        # self.send_artifact('rate/movies', 'movies', 'ratings')
        # self.send_artifact('movie/library', 'movies', 'collected')
        # self.send_artifact('movie/unlibrary', 'movies', 'missing.movies')

        self.save('last_artifacts', json_encode(self.artifacts))

        log.info('Finished pushing movies to trakt')
        return True

    def run_watched(self, key, p_movies, t_movie):
        return self.watch(key, p_movies, t_movie)

    def run_ratings(self, key, p_movies, t_movie):
        return self.rate(key, p_movies, t_movie)

    def run_collected(self, key, p_movies, t_movie):
        return self.collect(key, p_movies, t_movie)


class Push(Base):
    key = 'push'
    title = 'Push'
    children = [Show, Movie]
    threaded = True

    def run(self, *args, **kwargs):
        success = super(Push, self).run(*args, **kwargs)

        if kwargs.get('section') is None:
            # Update the status for each section
            for section in self.plex.sections():
                self.update_status(success, start_time=self.start_time, section=section.key)

        return success
