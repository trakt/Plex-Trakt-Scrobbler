from core.logger import Logger
from core.network import request, RequestError
from core.plugin import PLUGIN_VERSION
from core.helpers import all, total_seconds
from core.trakt_objects import TraktShow, TraktEpisode, TraktMovie
from datetime import datetime


log = Logger('core.trakt')

TRAKT_URL = 'http://api.trakt.tv/%s/ba5aa61249c02dc5406232da20f6e768f3c82b28%s'


class Trakt(object):
    @classmethod
    def request(cls, action, values=None, params=None, authenticate=False, retry=True, max_retries=3, timeout=None):
        if params is None:
            params = []
        elif isinstance(params, basestring):
            params = [params]

        params = [x for x in params if x]

        data_url = TRAKT_URL % (
            action,
            ('/' + '/'.join(params)) if params else ''
        )

        if authenticate:
            if values is None:
                values = {}

            values['username'] = Prefs['username']
            values['password'] = Hash.SHA1(Prefs['password'])
            values['plugin_version'] = PLUGIN_VERSION
            values['media_center_version'] = Dict['server_version']

        try:
            kwargs = {
                'retry': retry,
                'max_retries': max_retries,
                'timeout': timeout,

                'raise_exceptions': True
            }

            if values is not None:
                kwargs['data'] = values
                kwargs['data_type'] = 'json'

            response = request(data_url, 'json', **kwargs)
        except RequestError, e:
            Log.Warn('[trakt] Request error: (%s) %s' % (e, e.message))
            return {'success': False, 'exception': e, 'message': e.message}

        return cls.parse_response(response)

    @classmethod
    def parse_response(cls, response):
        if response is None:
            return {'success': False, 'message': 'Unknown Failure'}

        result = None

        # Return on successful results without status detail
        if type(response.data) is not dict or 'status' not in response.data:
            return {'success': True, 'data': response.data}

        status = response.data.get('status')

        if status == 'success':
            result = {'success': True, 'message': response.data.get('message', 'Unknown success')}
        elif status == 'failure':
            result = {'success': False, 'message': response.data.get('error'), 'data': response.data}

        # Log result for debugging
        message = result.get('message', 'Unknown Result')

        if not result.get('success'):
            Log.Warn('[trakt] Request failure: (%s) %s' % (result.get('exception'), message))

        return result

    class Account(object):
        @staticmethod
        def test():
            return Trakt.request('account/test', authenticate=True)

    class User(object):
        @classmethod
        def get_merged(cls, media, marked, include_ratings=False, extended=None, retry=True):
            start = datetime.now()

            # Fetch data from trakt
            library = cls.get_library(media, marked, extended=extended, retry=retry).get('data')

            ratings = None
            episode_ratings = None

            if include_ratings:
                ratings = cls.get_ratings(media, retry=retry).get('data')

                if media == 'shows':
                    episode_ratings = cls.get_ratings('episodes', retry=retry).get('data')

            # Merge data
            result = {}

            # Fill with watched items in library
            for item in library:
                key = Trakt.get_media_key(media, item)

                result[key] = Trakt.create_media(media, item, is_watched=True)

            # Merge ratings
            if include_ratings:
                for item in ratings:
                    key = Trakt.get_media_key(media, item)

                    if key not in result:
                        result[key] = Trakt.create_media(media, item)
                    else:
                        result[key].update(item)

            # Merge episode_ratings
            if include_ratings and media == 'shows':
                for item in episode_ratings:
                    key = Trakt.get_media_key(media, item['show'])

                    if key not in result:
                        result[key] = Trakt.create_media(media, item['show'])

                    episode = item['episode']
                    episode_key = (episode['season'], episode['number'])

                    if episode_key not in result[key].episodes:
                        result[key].episodes[episode_key] = TraktEpisode(episode['season'], episode['number'])

                    result[key].episodes[episode_key].update(item)

            elapsed = datetime.now() - start
            log.info('get_merged returned %s results in %s seconds', len(result), total_seconds(elapsed))

            return result

        @staticmethod
        def get_library(media, marked, extended=None, retry=True):
            return Trakt.request(
                'user/library/%s/%s.json' % (media, marked),
                params=[Prefs['username'], extended],

                retry=retry
            )

        @staticmethod
        def get_ratings(media, retry=True):
            return Trakt.request(
                'user/ratings/%s.json' % media,
                params=Prefs['username'],

                retry=retry
            )

    class Media(object):
        @staticmethod
        def action(media_type, action, retry=False, timeout=None, max_retries=3, **kwargs):
            if not all([x in kwargs for x in ['duration', 'progress', 'title']]):
                raise ValueError()

            # Retry scrobble requests as they are important (compared to watching requests)
            if action == 'scrobble':
                # Only change these values if they aren't already set
                retry = retry or True
                timeout = timeout or 3
                max_retries = 5

            return Trakt.request(
                media_type + '/' + action,
                kwargs,
                authenticate=True,

                retry=retry,
                max_retries=max_retries,
                timeout=timeout
            )

    @staticmethod
    def get_media_key(media, item):
        if item is None:
            return None

        if media == 'movies':
            return 'imdb', str(item.get('imdb_id'))

        if media == 'shows':
            return 'thetvdb', str(item.get('tvdb_id'))

        return None

    @classmethod
    def create_media(cls, media, info, is_watched=False):
        if media == 'shows':
            return TraktShow.create(info, is_watched=is_watched)

        if media == 'movies':
            return TraktMovie.create(info, is_watched=is_watched)

        raise ValueError('Unknown media type')
