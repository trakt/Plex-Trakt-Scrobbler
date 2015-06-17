from plugin.core.helpers.variable import dict_path
from plugin.models import *

from datetime import datetime
from trakt import Trakt
from trakt_sync.cache.main import Cache
import logging

GUID_AGENTS = [
    'imdb',
    'tvdb',

    'tmdb',
    'trakt',
    'tvrage'
]

log = logging.getLogger(__name__)


class SyncArtifacts(object):
    def __init__(self, task):
        self.task = task

        self.artifacts = {}

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

    def send(self):
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

                self.task.state.trakt.invalidate(data, media)

        if not changes:
            log.info('trakt.tv profile is up-to-date')
            return

        log.info('trakt.tv profile has been updated')

    @staticmethod
    def send_action(data, action, **kwargs):
        # Ensure items exist in `kwargs`
        if not kwargs:
            return False

        if not kwargs.get('movies') and not kwargs.get('shows'):
            return False

        # Try retrieve interface for `data`
        interface = Cache.Data.get_interface(data)

        if interface == 'sync/watched':
            # Watched add/remove functions are on the "sync/history" interface
            interface = 'sync/history'

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

    def store_episode(self, data, action, p_guid, identifier, p_show, **kwargs):
        key = (p_guid.agent, p_guid.sid)
        season_num, episode_num = identifier

        shows = dict_path(self.artifacts, [
            data,
            action,
            'shows'
        ])

        # Build show
        if key in shows:
            show = shows[key]
        else:
            show = self._build_request(p_guid, p_show)

            if show is None:
                return False

            # Store `show` in artifacts
            show['seasons'] = {}

            shows[key] = show

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

    def store_movie(self, data, action, p_guid, p_movie, **kwargs):
        key = (p_guid.agent, p_guid.sid)

        movies = dict_path(self.artifacts, [
            data,
            action,
            'movies'
        ])

        # Build movie
        if key in movies:
            movie = movies[key]
        else:
            movie = self._build_request(p_guid, p_movie, **kwargs)

            if movie is None:
                return False

            # Store `movie` in artifacts
            movies[key] = movie

        # Set `kwargs` on `movie`
        self._set_kwargs(movie, kwargs)
        return True

    @classmethod
    def _build_request(cls, p_guid, p_item, **kwargs):
        # Validate parameters
        if not p_item.get('title') or not p_item.get('year'):
            log.warn('Invalid "title" or "year" attribute on <%r (%r)>', p_item.get('title'), p_item.get('year'))
            return None

        if not p_guid:
            log.warn('Invalid GUID attribute on <%r (%r)>', p_item.get('title'), p_item.get('year'))
            return None

        if p_guid.agent not in GUID_AGENTS:
            log.warn('GUID agent %r is not supported on <%r (%r)>', p_guid.agent, p_item.get('title'), p_item.get('year'))
            return None

        # Build request
        request = {
            'title': p_item['title'],
            'year': p_item['year'],

            'ids': {}
        }

        # Set identifier
        request['ids'][p_guid.agent] = p_guid.sid

        # Set extra attributes
        cls._set_kwargs(request, kwargs)

        return request

    @staticmethod
    def _set_kwargs(request, kwargs):
        for key, value in kwargs.items():
            if type(value) is datetime:
                try:
                    # Convert `datetime` object to string
                    value = value.strftime('%Y-%m-%dT%H:%M:%S') + '.000-00:00'
                except Exception, ex:
                    log.warn('Unable to convert %r to string', value)
                    return False

            request[key] = value

        return True
