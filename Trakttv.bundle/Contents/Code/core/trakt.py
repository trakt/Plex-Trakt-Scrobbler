from core.logger import Logger
from core.network import request, RequestError
from core.plugin import PLUGIN_VERSION
from core.helpers import all, total_seconds
from core.trakt_objects import TraktShow, TraktEpisode, TraktMovie
from datetime import datetime


log = Logger('core.trakt')

TRAKT_URL = 'http://api.trakt.tv/%s/ba5aa61249c02dc5406232da20f6e768f3c82b28%s'


IDENTIFIERS = {
    'movies': {
        ('imdb_id', 'imdb'),
        ('tmdb_id', 'themoviedb')
    },
    'shows': [
        ('tvdb_id', 'thetvdb'),
        ('imdb_id', 'imdb'),
        ('tvrage_id', 'tvrage')
    ]
}


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
            log.warn('[trakt] Request error: (%s) %s' % (e, e.message))
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
            log.warn('[trakt] Request failure: (%s) %s' % (result.get('exception'), message))

        return result

    class Account(object):
        @staticmethod
        def test():
            return Trakt.request('account/test', authenticate=True)

    class User(object):
        @classmethod
        def get_merged(cls, media, watched=True, ratings=False, collected=False, extended=None, retry=True):
            start = datetime.utcnow()

            # Merge data
            result = {}

            # Merge watched library
            if watched and not Trakt.merge_watched(result, media, extended, retry):
                log.warn('Failed to merge watched library')
                return None

            # Merge ratings
            if ratings and not Trakt.merge_ratings(result, media, retry):
                log.warn('Failed to merge ratings')
                return None

            # Merge collected library
            if collected and not Trakt.merge_collected(result, media, extended, retry):
                log.warn('Failed to merge collected library')
                return None

            item_count = len(result)

            # Generate entries for alternative keys
            for key, item in result.items():
                # Skip first key (because it's the root_key)
                for alt_key in item.keys[1:]:
                    result[alt_key] = item

            elapsed = datetime.utcnow() - start

            log.debug(
                'get_merged returned dictionary with %s keys for %s items in %s seconds',
                len(result), item_count, total_seconds(elapsed)
            )

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
    def get_media_keys(media, item):
        if item is None:
            return None

        result = []

        for t_key, p_key in IDENTIFIERS[media]:
            result.append((p_key, str(item.get(t_key))))

        if not len(result):
            return None, []

        return result[0], result

    @classmethod
    def create_media(cls, media, keys, info, is_watched=None, is_collected=None):
        if media == 'shows':
            return TraktShow.create(keys, info, is_watched, is_collected)

        if media == 'movies':
            return TraktMovie.create(keys, info, is_watched, is_collected)

        raise ValueError('Unknown media type')

    @classmethod
    def merge_watched(cls, result, media, extended=None, retry=True):
        watched = cls.User.get_library(media, 'watched', extended=extended, retry=retry).get('data')

        if watched is None:
            log.warn('Unable to fetch watched library from trakt')
            return False

        # Fill with watched items in library
        for item in watched:
            root_key, keys = Trakt.get_media_keys(media, item)

            result[root_key] = Trakt.create_media(media, keys, item, is_watched=True)

        return True

    @classmethod
    def merge_ratings(cls, result, media, retry=True):
        ratings = cls.User.get_ratings(media, retry=retry).get('data')
        episode_ratings = None

        if media == 'shows':
            episode_ratings = cls.User.get_ratings('episodes', retry=retry).get('data')

        if ratings is None or (media == 'shows' and episode_ratings is None):
            log.warn('Unable to fetch ratings from trakt')
            return False

        # Merge ratings
        for item in ratings:
            root_key, keys = Trakt.get_media_keys(media, item)

            if root_key not in result:
                result[root_key] = Trakt.create_media(media, keys, item)
            else:
                result[root_key].fill(item)

        # Merge episode_ratings
        if media == 'shows':
            for item in episode_ratings:
                root_key, keys = Trakt.get_media_keys(media, item['show'])

                if root_key not in result:
                    result[root_key] = Trakt.create_media(media, keys, item['show'])

                episode = item['episode']
                episode_key = (episode['season'], episode['number'])

                if episode_key not in result[root_key].episodes:
                    result[root_key].episodes[episode_key] = TraktEpisode.create(episode['season'], episode['number'])

                result[root_key].episodes[episode_key].fill(item)

        return True


    @classmethod
    def merge_collected(cls, result, media, extended=None, retry=True):
        collected = Trakt.User.get_library(media, 'collection', extended=extended, retry=retry).get('data')

        if collected is None:
            log.warn('Unable to fetch collected library from trakt')
            return False

        # Merge ratings
        for item in collected:
            root_key, keys = Trakt.get_media_keys(media, item)

            if root_key not in result:
                result[root_key] = Trakt.create_media(media, keys, item, is_collected=True)
            else:
                result[root_key].update_states(is_collected=True)

        return True
