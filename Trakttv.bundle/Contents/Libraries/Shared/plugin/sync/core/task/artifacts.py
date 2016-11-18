from plugin.core.constants import GUID_SERVICES
from plugin.core.helpers.variable import dict_path
from plugin.models import *
from plugin.preferences import Preferences
from plugin.sync.core.enums import SyncActionMode, SyncData

from datetime import datetime, timedelta
from trakt import Trakt
from trakt_sync.cache.main import Cache
import elapsed
import logging

log = logging.getLogger(__name__)


class SyncArtifacts(object):
    def __init__(self, task):
        self.task = task

        self.artifacts = {}

    #
    # Log/Send artifacts
    #

    def send(self):
        action_mode = self.task.configuration['sync.action.mode']

        if action_mode == SyncActionMode.Update:
            self.send_actions()
            return True

        if action_mode == SyncActionMode.Log:
            self.log_actions()
            return True

        raise NotImplementedError('Unable to send artifacts to trakt, action mode %r not supported', action_mode)

    @elapsed.clock
    def send_actions(self):
        changes = False

        for data, action, request in self.flatten():
            changes = True

            # Send artifact to trakt.tv
            self.send_action(data, action, **request)

            # Invalidate cache to ensure actions aren't resent
            for key, value in request.items():
                if not value:
                    # Empty media request
                    continue

                if key == 'shows':
                    media = Cache.Media.Shows
                elif key == 'movies':
                    media = Cache.Media.Movies
                else:
                    # Unknown media type
                    continue

                self.task.state.trakt.invalidate(
                    Cache.Media.get(media),
                    Cache.Data.get(data)
                )

            # Task checkpoint
            self.task.checkpoint()

        if not changes:
            log.info('trakt.tv profile is up-to-date')
            return

        log.info('trakt.tv profile has been updated')

    @classmethod
    def send_action(cls, data, action, **kwargs):
        # Ensure items exist in `kwargs`
        if not kwargs:
            return False

        if not kwargs.get('movies') and not kwargs.get('shows'):
            return False

        # Try retrieve interface for `data`
        interface = cls._get_interface(data)

        if interface is None:
            log.warn('[%s](%s) Unknown data type', data, action)
            return False

        # Try retrieve method for `action`
        func = getattr(Trakt[interface], action, None)

        if func is None:
            log.warn('[%s](%s) Unable find action in interface', data, action)
            return False

        # Send request to trakt.tv
        response = func(kwargs)

        if response is None:
            return False

        log.debug('[%s](%s) Response: %r', data, action, response)
        return True

    def log_actions(self):
        for data, action, request in self.flatten():
            # Try retrieve interface for `data`
            interface = self._get_interface(data)

            if interface is None:
                log.warn('[%s](%s) Unknown data type', data, action)
                continue

            # Log request items
            for media, items in request.items():
                self.log_items(interface, action, media, items)

    def log_items(self, interface, action, media, items):
        if not items:
            return

            # Log each item
        for item in items:
            if not item:
                continue

            log.info('[%s:%s](%s) %r (%r)', interface, action, media, item.get('title'), item.get('year'))

            if media == 'shows':
                # Log each episode
                self.log_episodes(item)

    def log_episodes(self, item):
        for season in item.get('seasons', []):
            episodes = season.get('episodes')

            if episodes is None:
                log.info('    S%02d', season.get('number'))
                continue

            for episode in episodes:
                log.info('    S%02dE%02d', season.get('number'), episode.get('number'))

    @staticmethod
    def _get_interface(data):
        # Try retrieve interface for `data`
        interface = Cache.Data.get_interface(data)

        if interface == 'sync/watched':
            # Watched add/remove functions are on the "sync/history" interface
            return 'sync/history'

        return interface

    #
    # Artifact storage
    #

    def store_show(self, data, action, guid, p_show=None, **kwargs):
        key = (guid.service, guid.id)

        shows = dict_path(self.artifacts, [
            data,
            action,
            'shows'
        ])

        # Build show
        if key in shows:
            show = shows[key]
        else:
            show = self._build_request(guid, p_show, **kwargs)

            if show is None:
                return False

            # Store `show` in artifacts
            shows[key] = show

        # Set `kwargs` on `show`
        self._set_kwargs(show, kwargs)
        return True

    def store_episode(self, data, action, guid, identifier, p_key=None, p_show=None, p_episode=None, **kwargs):
        key = (guid.service, guid.id)
        season_num, episode_num = identifier

        shows = dict_path(self.artifacts, [
            data,
            action,
            'shows'
        ])

        # Check for duplicate history addition
        if self._is_duplicate(data, action, p_key):
            return False

        # Build show
        if key in shows:
            show = shows[key]
        else:
            show = self._build_request(guid, p_show)

            if show is None:
                return False

            shows[key] = show

        # Ensure 'seasons' attribute exists
        if 'seasons' not in show:
            show['seasons'] = {}

        # Build season
        if season_num in show['seasons']:
            season = show['seasons'][season_num]
        else:
            season = show['seasons'][season_num] = {'number': season_num}
            season['episodes'] = {}

        # Build episode
        if episode_num in season['episodes']:
            episode = season['episodes'][episode_num]
        else:
            episode = season['episodes'][episode_num] = {'number': episode_num}

        # Set `kwargs` on `episode`
        self._set_kwargs(episode, kwargs)
        return True

    def store_movie(self, data, action, guid, p_key=None, p_movie=None, **kwargs):
        key = (guid.service, guid.id)

        movies = dict_path(self.artifacts, [
            data,
            action,
            'movies'
        ])

        # Check for duplicate history addition
        if self._is_duplicate(data, action, p_key):
            return False

        # Build movie
        if key in movies:
            movie = movies[key]
        else:
            movie = self._build_request(guid, p_movie, **kwargs)

            if movie is None:
                return False

            # Store `movie` in artifacts
            movies[key] = movie

        # Set `kwargs` on `movie`
        self._set_kwargs(movie, kwargs)
        return True

    @classmethod
    def _build_request(cls, guid, p_item, **kwargs):
        # Validate request
        if not cls._validate_request(guid, p_item):
            return None

        # Build request
        request = {
            'ids': {}
        }

        # Set identifier
        request['ids'][guid.service] = guid.id

        # Set extra attributes
        cls._set_kwargs(request, kwargs)

        return request

    def _is_duplicate(self, data, action, p_key):
        if data != SyncData.Watched or action != 'add':
            return False

        # Retrieve scrobble duplication period
        duplication_period = Preferences.get('scrobble.duplication_period')

        if duplication_period is None:
            return False

        # Check for duplicate scrobbles in `duplication_period`
        # TODO check `part` attribute
        scrobbled = ActionHistory.has_scrobbled(
            self.task.account, p_key,
            after=datetime.utcnow() - timedelta(minutes=duplication_period)
        )

        if scrobbled:
            log.info(
                'Ignoring duplicate history addition, scrobble already performed in the last %d minutes',
                duplication_period
            )
            return True

        return False

    @classmethod
    def _validate_request(cls, guid, p_item):
        # Build item identifier
        if p_item:
            identifier = '<%r (%r)>' % (p_item.get('title'), p_item.get('year'))
        else:
            identifier = repr(guid)

        # Validate parameters
        if p_item is not None and (not p_item.get('title') or not p_item.get('year')):
            log.info('Invalid "title" or "year" attribute on %s', identifier)
            return False

        if not guid or not guid.valid:
            log.warn('Invalid GUID attribute on %s (guid: %r)', identifier, guid)
            return False

        if guid.service not in GUID_SERVICES:
            log.warn('GUID service %r is not supported on %s', guid.service if guid else None, identifier)
            return False

        return True

    @staticmethod
    def _set_kwargs(request, kwargs):
        for key, value in kwargs.items():
            if type(value) is datetime:
                try:
                    # Convert `datetime` object to string
                    value = value.strftime('%Y-%m-%dT%H:%M:%S') + '.000-00:00'
                except Exception:
                    log.warn('Unable to convert %r to string', value)
                    return False

            request[key] = value

        return True

    #
    # Flatten
    #

    def flatten(self):
        for data, actions in self.artifacts.items():
            for action, request in actions.items():
                if 'shows' in request:
                    request['shows'] = list(self.flatten_shows(request['shows']))

                if 'movies' in request:
                    request['movies'] = request['movies'].values()

                yield data, action, request

    @staticmethod
    def flatten_shows(shows):
        for show in shows.itervalues():
            if 'seasons' not in show:
                yield show
                continue

            show['seasons'] = show['seasons'].values()

            for season in show['seasons']:
                if 'episodes' not in season:
                    continue

                season['episodes'] = season['episodes'].values()

            yield show
