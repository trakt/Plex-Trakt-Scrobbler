from core.network import request, RequestError
from core.plugin import PLUGIN_VERSION
from core.helpers import all


TRAKT_URL = 'http://api.trakt.tv/%s/ba5aa61249c02dc5406232da20f6e768f3c82b28%s'


class Trakt(object):
    @classmethod
    def request(cls, action, values=None, params=None, authenticate=False, retry=True, max_retries=3, timeout=None):
        if isinstance(params, basestring):
            params = [params]

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
        @staticmethod
        def get_library(media, marked, extended='min', retry=True):
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
