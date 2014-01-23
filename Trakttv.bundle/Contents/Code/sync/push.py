from core.helpers import all, try_convert, merge, plural
from core.logger import Logger
from core.trakt import Trakt
from plex.plex_objects import PlexEpisode
from sync.sync_base import SyncBase


log = Logger('sync.push')


class Base(SyncBase):
    task = 'push'

    @staticmethod
    def get_root(p_item):
        if isinstance(p_item, PlexEpisode):
            return p_item.parent

        return p_item

    @staticmethod
    def add_identifier(data, p_item):
        service, sid = p_item.key

        # Parse identifier and append relevant '*_id' attribute to data
        if service == 'imdb':
            data['imdb_id'] = sid
            return data

        # Convert TMDB and TVDB identifiers to integers
        if service in ['themoviedb', 'thetvdb']:
            sid = try_convert(sid, int)

            # If identifier is invalid, ignore it
            if sid is None:
                return data

        if service == 'themoviedb':
            data['tmdb_id'] = sid

        if service == 'thetvdb':
            data['tvdb_id'] = sid

        return data

    @classmethod
    def get_trakt_data(cls, p_item, include_identifier=True):
        data = {}

        # Append episode attributes if this is a PlexEpisode
        if isinstance(p_item, PlexEpisode):
            data.update({
                'season': p_item.season_num,
                'episode': p_item.episode_num
            })

        if include_identifier:
            p_root = cls.get_root(p_item)

            data.update({
                'title': p_root.title,
                'year': p_root.year
            })

            cls.add_identifier(data, p_root)

        return data

    def watch(self, p_items, t_item, include_identifier=True):
        if type(p_items) is not list:
            p_items = [p_items]

        # Ignore if trakt movie is already watched
        if t_item and t_item.is_watched:
            return True

        # Ignore if none of the plex items are watched
        if all([not x.seen for x in p_items]):
            return True

        # TODO should we instead pick the best result, instead of just the first?
        self.store('watched', self.get_trakt_data(p_items[0], include_identifier))

    def rate(self, p_items, t_item, artifact='ratings'):
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

        data = self.get_trakt_data(p_item)

        data.update({
            'rating': p_item.user_rating
        })

        self.store(artifact, data)
        return True

    def collect(self, p_items, t_item, include_identifier=True):
        if type(p_items) is not list:
            p_items = [p_items]

        # Ignore if trakt movie is already collected
        if t_item and t_item.is_collected:
            return True

        self.store('collected', self.get_trakt_data(p_items[0], include_identifier))
        return True

    def store_episodes(self, show, key, artifact=None):
        episodes = self.child('episode').artifacts.get(artifact or key)

        if episodes is None:
            return

        self.store(key, merge({'episodes': episodes}, show))

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
        if items is None:
            return

        return self.send(action, {key: items})


class Episode(Base):
    key = 'episode'
    auto_run = False

    def run(self, p_episodes, t_episodes):
        self.reset()

        enabled_funcs = self.get_enabled_functions()

        for key, p_episode in p_episodes.items():
            t_episode = t_episodes.get(key)

            # TODO check result
            self.trigger(enabled_funcs, key=key, p_episode=p_episode, t_episode=t_episode)

        return True

    def run_watched(self, key, p_episode, t_episode):
        return self.watch(p_episode, t_episode, include_identifier=False)

    def run_ratings(self, key, p_episode, t_episode):
        return self.parent.rate(p_episode, t_episode, 'episode_ratings')

    def run_collected(self, key, p_episode, t_episode):
        return self.collect(p_episode, t_episode, include_identifier=False)


class Show(Base):
    key = 'show'
    children = [Episode]

    def run(self, section=None):
        # TODO use 'section' parameter
        self.reset()

        enabled_funcs = self.get_enabled_functions()

        p_shows = self.plex.library('show')

        # Fetch library, and only get ratings and collection if enabled
        t_shows = self.trakt.merged(
            'shows',
            ratings='ratings' in enabled_funcs,
            collected='collected' in enabled_funcs
        )

        if t_shows is None:
            log.warn('Unable to construct merged library from trakt')
            return False

        for key, p_show in p_shows.items():
            t_show = t_shows.get(key)

            log.debug('Processing "%s" [%s]', p_show[0].title if p_show else None, key)

            # TODO check result
            self.trigger(enabled_funcs, key=key, p_shows=p_show, t_show=t_show)

            for p_show in p_show:
                self.child('episode').run(
                    p_episodes=self.plex.episodes(p_show.rating_key, p_show),
                    t_episodes=t_show.episodes if t_show else {}
                )

                show = self.get_trakt_data(p_show)

                self.store_episodes(show, 'collected')
                self.store_episodes(show, 'watched')

        # Push changes to trakt
        for show in self.retrieve('collected'):
            self.send('show/episode/library', show)

        for show in self.retrieve('watched'):
            self.send('show/episode/seen', show)

        self.send_artifact('rate/shows', 'shows', 'ratings')
        self.send_artifact('rate/episodes', 'episodes', 'episode_ratings')

        log.info('Finished pushing shows to trakt')
        return True

    def run_ratings(self, key, p_shows, t_show):
        return self.rate(p_shows, t_show)


class Movie(Base):
    key = 'movie'

    def run(self, section=None):
        # TODO use 'section' parameter
        self.reset()

        enabled_funcs = self.get_enabled_functions()

        p_movies = self.plex.library('movie')

        # Fetch library, and only get ratings and collection if enabled
        t_movies = self.trakt.merged(
            'movies',
            ratings='ratings' in enabled_funcs,
            collected='collected' in enabled_funcs
        )

        if t_movies is None:
            log.warn('Unable to construct merged library from trakt')
            return False

        for key, p_movie in p_movies.items():
            t_movie = t_movies.get(key)

            log.debug('Processing "%s" [%s]', p_movie[0].title if p_movie else None, key)

            # TODO check result
            self.trigger(enabled_funcs, key=key, p_movies=p_movie, t_movie=t_movie)

        # Push changes to trakt
        self.send_artifact('movie/seen', 'movies', 'watched')
        self.send_artifact('rate/movies', 'movies', 'ratings')
        self.send_artifact('movie/library', 'movies', 'collected')

        log.info('Finished pushing movies to trakt')
        return True

    def run_watched(self, key, p_movies, t_movie):
        return self.watch(p_movies, t_movie)

    def run_ratings(self, key, p_movies, t_movie):
        return self.rate(p_movies, t_movie)

    def run_collected(self, key, p_movies, t_movie):
        return self.collect(p_movies, t_movie)


class Push(Base):
    key = 'push'
    title = 'Push'
    children = [Show, Movie]
