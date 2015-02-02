from core.action import ActionHelper
from core.helpers import all, json_encode, merge
from core.logger import Logger
from data.watch_session import WatchSession
from pts.action_manager import ActionManager
from sync.sync_base import SyncBase

from datetime import datetime
from plex_metadata import Library
from trakt import Trakt


log = Logger('sync.push')


class Base(SyncBase):
    task = 'push'

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
        if WatchSession.is_active(p_items[0].rating_key):
            log.trace('[P #%s] ignored - item is currently being watched', p_items[0].rating_key)
            return True

        # Build item which can be sent to trakt
        item = ActionHelper.plex.to_trakt(key, p_items[0])

        if not item:
            log.warn('watch() - Ignored for unmatched media "%s" [%s]', p_items[0].title, key)
            return True

        # Check action against history
        history = ActionManager.history.get(p_items[0].rating_key, {})

        if not ActionManager.valid_action('add', history):
            log.debug('watch() - Invalid action for "%s" [%s] (already scrobbled or duplicate action)', p_items[0].title, key)
            return True

        # Mark item as added in `pts.action_manager`
        ActionManager.update_history(p_items[0].rating_key, 'add', 'add')

        # Set "watched_at" parameter (if available)
        watched_at = self.get_datetime(p_items[0], 'last_viewed_at')

        if watched_at:
            item['watched_at'] = watched_at

        # Store item in "watched" collection
        self.store('watched', item)

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
        if t_item and t_item.rating and int(t_item.rating.value) == int(p_item.user_rating):
            return True if artifact else {}

        if include_metadata:
            data = ActionHelper.plex.to_trakt(key, p_item)

            if not data:
                log.warn('rate() - Ignored for unmatched media "%s" [%s]', p_item.title, key)
                return True if artifact else {}
        else:
            data = {}

        data.update({
            'rating': int(p_item.user_rating)
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

        # Build item which can be sent to trakt
        item = ActionHelper.plex.to_trakt(key, p_items[0])

        if not item:
            log.warn('collect() - Ignored for unmatched media "%s" [%s]', p_items[0].title, key)
            return True

        # Set "watched_at" parameter (if available)
        collected_at = self.get_datetime(p_items[0], 'added_at')

        if collected_at:
            item['collected_at'] = collected_at

        # Store item in "watched" collection
        self.store('collected', item)

        return True

    @staticmethod
    def get_datetime(p_item, key):
        value = getattr(p_item, key, None)

        if not value:
            return None

        try:
            # Construct datetime from UTC Timestamp
            dt = datetime.utcfromtimestamp(value)

            # Return formatted datetime for trakt.tv
            return dt.strftime('%Y-%m-%dT%H:%M:%S') + '.000-00:00'
        except Exception, ex:
            log.error('Unable to construct datetime from timestamp: %s (%s: %r)', ex, key, value)
            return None

    def add(self, path, **kwargs):
        log.debug('[%s] Adding items: %s', path, kwargs)

        if not kwargs.get('movies') and not kwargs.get('shows'):
            # Empty request
            return

        response = Trakt[path].add(kwargs, exceptions=True)

        if not response:
            log.warn('[%s] Request failed', path)
            return

        self.log_response(path, response)

    def remove(self, path, **kwargs):
        log.debug('[%s] Removing items: %s', path, kwargs)

        if not kwargs.get('movies') and not kwargs.get('shows'):
            # Empty request
            return

        response = Trakt[path].remove(kwargs, exceptions=True)

        if not response:
            log.warn('[%s] Request failed', path)
            return

        self.log_response(path, response)

    def log_response(self, path, response):
        log.debug('[%s] Response: %r', path, response)

        # Print "not_found" items (if any)
        not_found = response.get('not_found', {})

        for media, items in not_found.items():
            if media in ['seasons', 'episodes']:
                # Print missing seasons
                for show in items:
                    if not show.get('seasons'):
                        # Print show that is missing
                        log.warn('[%s](%s) Unable to find %r', path, media, show.get('title'))
                        continue

                    for season in show['seasons']:
                        if not season.get('episodes'):
                            # Print season that is missing
                            log.warn('[%s](%s) Unable to find %r S%02d', path, media, show.get('title'), season.get('number'))
                            continue

                        # Print season episodes that are missing
                        log.warn('[%s](%s) Unable to find %r S%02d %s', path, media, show.get('title'), season.get('number'), ', '.join([
                            'E%02d' % episode.get('number')
                            for episode in season.get('episodes')
                        ]))
            elif media == 'movies':
                # Print missing movies
                for item in items:
                    log.warn('[%s](%s) Unable to find %r', path, media, item.get('title'))
            else:
                # Print missing items
                for item in items:
                    log.warn('[%s](%s) Unable to find %r', path, media, item)

        # Print "deleted" items
        deleted = response.get('deleted', {})

        if deleted.get('movies'):
            log.info('[%s] Deleted %s movie(s)', path, deleted['movies'])
        elif deleted.get('episodes'):
            log.info('[%s] Deleted %s episode(s)', path, deleted['episodes'])

        # Print "added" items
        added = response.get('added', {})

        if added.get('movies'):
            log.info('[%s] Added %s movie(s)', path, added['movies'])
        elif added.get('episodes'):
            log.info('[%s] Added %s episode(s)', path, added['episodes'])

        # Print "existing" items
        existing = response.get('existing', {})

        if existing.get('movies'):
            log.info('[%s] Ignored %s existing movie(s)', path, existing['movies'])
        elif existing.get('episodes'):
            log.info('[%s] Ignored %s existing episode(s)', path, existing['episodes'])


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

        for x, (key, p_shows) in enumerate(p_shows.items()):
            self.check_stopping()
            self.emit('progress', x + 1)

            t_show = t_shows_table.get(key)

            log.debug('Processing "%s" [%s]', p_shows[0].title if p_shows else None, key)

            # TODO check result
            self.trigger(enabled_funcs, key=key, p_shows=p_shows, t_show=t_show)

            show = None
            show_artifacts = {
                'collected': [],
                'watched': [],
                'ratings': []
            }

            for p_show in p_shows:
                if not show:
                    # Build data from plex show
                    data = ActionHelper.plex.to_trakt(key, p_show)

                    if data:
                        # Valid show, use data
                        show = data
                    else:
                        log.warn('Ignored unmatched show "%s" [%s]', p_show.title if p_show else None, key)
                        continue

                # Run season task
                self.child('season').run(
                    p_seasons=Library.episodes(p_show.rating_key, p_show, flat=False),
                    t_seasons=t_show.seasons if t_show else {},
                    artifacts=artifacts
                )

                # Store season artifacts
                show_artifacts['collected'].append(
                    self.child('season').artifacts.pop('collected', [])
                )

                show_artifacts['watched'].append(
                    self.child('season').artifacts.pop('watched', [])
                )

                show_artifacts['ratings'].append(
                    self.child('season').artifacts.pop('ratings', [])
                )

            if not show:
                log.warn('Unable to retrieve show details, ignoring "%s" [%s]', p_show.title if p_show else None, key)
                continue

            # Merge show artifacts
            for k, v in show_artifacts.items():
                result = []

                for seasons in v:
                    result = self.merge_artifacts(result, seasons)

                show_artifacts[k] = result

            # Store merged artifacts
            self.store_seasons('collected', show, seasons=show_artifacts.get('collected'))
            self.store_seasons('watched', show, seasons=show_artifacts.get('watched'))

            show_rating = self.rate(key, p_shows, t_show, artifact='', include_metadata=False)

            self.store_seasons('ratings', merge(
                # Include show rating
                show_rating,
                show
            ), seasons=show_artifacts.get('ratings'))

        self.emit('finished')
        self.check_stopping()

        #
        # Push changes to trakt
        #
        self.add('sync/collection', shows=self.retrieve('collected'))
        self.add('sync/history', shows=self.retrieve('watched'))
        self.add('sync/ratings', shows=self.retrieve('ratings'))

        self.remove('sync/collection', shows=self.retrieve('missing.shows'))

        self.save('last_artifacts', json_encode(self.artifacts))

        log.info('Finished pushing shows to trakt')
        return True

    @classmethod
    def merge_artifacts(cls, a, b, mode='seasons'):
        result = []

        # Build 'number'-maps from lists
        a = dict([(x.get('number'), x) for x in a])
        b = dict([(x.get('number'), x) for x in b])

        # Build key sets
        a_keys = set(a.keys())
        b_keys = set(b.keys())

        # Insert items that don't conflict
        for key in a_keys - b_keys:
            result.append(a[key])

        for key in b_keys - a_keys:
            result.append(b[key])

        # Resolve conflicts
        for key in a_keys & b_keys:
            a_item = a[key]
            b_item = b[key]

            if mode == 'seasons':
                # Merge episodes
                episodes = cls.merge_artifacts(a_item['episodes'], b_item['episodes'], mode='episodes')

                # Use the item from `a` and merged episodes list
                item = a_item
                item['episodes'] = episodes
            else:
                # Use the item from `a`
                item = a_item

            result.append(item)

        return result


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
        self.add('sync/collection', movies=self.retrieve('collected'))
        self.add('sync/history', movies=self.retrieve('watched'))
        self.add('sync/ratings', movies=self.retrieve('ratings'))

        self.remove('sync/collection', movies=self.retrieve('missing.movies'))

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
