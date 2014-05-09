from core.helpers import all, plural, json_encode
from core.logger import Logger
from core.trakt import Trakt
from sync.sync_base import SyncBase


log = Logger('sync.push')


class Base(SyncBase):
    task = 'push'

    def watch(self, key, p_items, t_item, include_identifier=True):
        if type(p_items) is not list:
            p_items = [p_items]

        # Ignore if trakt movie is already watched
        if t_item and t_item.is_watched:
            return True

        # Ignore if none of the plex items are watched
        if all([not x.seen for x in p_items]):
            return True

        # TODO should we instead pick the best result, instead of just the first?
        self.store('watched', self.plex.to_trakt(key, p_items[0], include_identifier))

    def rate(self, key, p_items, t_item, artifact='ratings'):
        if type(p_items) is not list:
            p_items = [p_items]

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

        data = self.plex.to_trakt(key, p_item)

        data.update({
            'rating': p_item.user_rating
        })

        self.store(artifact, data)
        return True

    def collect(self, key, p_items, t_item, include_identifier=True):
        if type(p_items) is not list:
            p_items = [p_items]

        # Ignore if trakt movie is already collected
        if t_item and t_item.is_collected:
            return True

        self.store('collected', self.plex.to_trakt(key, p_items[0], include_identifier))
        return True

    @staticmethod
    def log_artifact(action, label, count, level='info'):
        message = '(%s) %s %s item%s' % (
            action, label, count,
            plural(count)
        )

        if level == 'info':
            return log.info(message)
        elif level == 'warn':
            return log.warn(message)

        raise ValueError('Unknown level specified')

    def send(self, action, data):
        response = Trakt.request(action, data, authenticate=True)

        # Log successful items
        if 'rated' in response:
            rated = response.get('rated')
            unrated = response.get('unrated')

            log.info(
                '(%s) Rated %s item%s and un-rated %s item%s',
                action,
                rated, plural(rated),
                unrated, plural(unrated)
            )
        elif 'message' in response:
            log.info('(%s) %s', action, response['message'])
        else:
            self.log_artifact(action, 'Inserted', response.get('inserted'))

        # Log skipped items, if there were any
        skipped = response.get('skipped', 0)

        if skipped > 0:
            self.log_artifact(action, 'Skipped', skipped, level='warn')

    def send_artifact(self, action, key, artifact):
        items = self.artifacts.get(artifact)
        if not items:
            return

        return self.send(action, {key: items})


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
        return self.watch(key, p_episode, t_episode, include_identifier=False)

    def run_ratings(self, key, p_episode, t_episode):
        return self.parent.rate(key, p_episode, t_episode, 'episode_ratings')

    def run_collected(self, key, p_episode, t_episode):
        return self.collect(key, p_episode, t_episode, include_identifier=False)


class Show(Base):
    key = 'show'
    children = [Episode]

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

        self.start(len(p_shows))

        for x, (key, p_show) in enumerate(p_shows.items()):
            self.check_stopping()
            self.progress(x + 1)

            t_show = t_shows_table.get(key)

            log.debug('Processing "%s" [%s]', p_show[0].title if p_show else None, key)

            # TODO check result
            self.trigger(enabled_funcs, key=key, p_shows=p_show, t_show=t_show)

            for p_show in p_show:
                self.child('episode').run(
                    p_episodes=self.plex.episodes(p_show.rating_key, p_show),
                    t_episodes=t_show.episodes if t_show else {},
                    artifacts=artifacts
                )

                show = self.plex.to_trakt(key, p_show)

                self.store_episodes('collected', show)
                self.store_episodes('watched', show)

        self.finish()
        self.check_stopping()

        #
        # Push changes to trakt
        #
        for show in self.retrieve('collected'):
            self.send('show/episode/library', show)

        for show in self.retrieve('watched'):
            self.send('show/episode/seen', show)

        self.send_artifact('rate/shows', 'shows', 'ratings')
        self.send_artifact('rate/episodes', 'episodes', 'episode_ratings')

        for show in self.retrieve('missing.shows'):
            self.send('show/unlibrary', show)

        for show in self.retrieve('missing.episodes'):
            self.send('show/episode/unlibrary', show)

        self.save('last_artifacts', json_encode(self.artifacts))

        log.info('Finished pushing shows to trakt')
        return True

    def run_ratings(self, key, p_shows, t_show):
        return self.rate(key, p_shows, t_show)


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

        self.start(len(p_movies))

        for x, (key, p_movie) in enumerate(p_movies.items()):
            self.check_stopping()
            self.progress(x + 1)

            t_movie = t_movies_table.get(key)

            log.debug('Processing "%s" [%s]', p_movie[0].title if p_movie else None, key)

            # TODO check result
            self.trigger(enabled_funcs, key=key, p_movies=p_movie, t_movie=t_movie)

        self.finish()
        self.check_stopping()

        #
        # Push changes to trakt
        #
        self.send_artifact('movie/seen', 'movies', 'watched')
        self.send_artifact('rate/movies', 'movies', 'ratings')
        self.send_artifact('movie/library', 'movies', 'collected')
        self.send_artifact('movie/unlibrary', 'movies', 'missing.movies')

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
            for (_, k, _) in self.plex.sections():
                self.update_status(True, start_time=self.start_time, section=k)

        return success
