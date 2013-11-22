from core.network import request, RequestError
from core.plugin import PLUGIN_VERSION
from core.helpers import all
import socket
import time


TRAKT_URL = 'http://api.trakt.tv/%s/ba5aa61249c02dc5406232da20f6e768f3c82b28%s'


class Trakt(object):
    retry_codes = [408, 500, (502, 504), 522, 524, (598, 599)]

    @classmethod
    def can_retry(cls, error_code):
        for retry_code in cls.retry_codes:
            if type(retry_code) is tuple and len(retry_code) == 2:
                if retry_code[0] <= error_code <= retry_code[1]:
                    return True
            elif type(retry_code) is int:
                if retry_code == error_code:
                    return True
            else:
                raise ValueError("Invalid retry_code specified: %s" % retry_code)

        return False

    @classmethod
    def request(cls, action, values=None, param=''):
        if param != "":
            param = "/" + param
        data_url = TRAKT_URL % (action, param)

        if values is None:
            values = {}

        values['username'] = Prefs['username']
        values['password'] = Hash.SHA1(Prefs['password'])
        values['plugin_version'] = PLUGIN_VERSION
        values['media_center_version'] = Dict['server_version']

        result = None

        try:
            response = request(data_url, 'json', data=values, data_type='json', raise_exceptions=True)
        except RequestError, e:
            Log.Warn('[trakt] Request error: (%s) %s' % (result.get('exception'), result.get('message')))
            return {'success': False, 'exception': e, 'message': e.message}

        return cls.parse_response(response)

    @classmethod
    def parse_response(cls, response):
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

    # TODO this needs updating
    @classmethod
    def request_retry(cls, action, values=None, param='', max_retries=3, retry_sleep=5):
        result = cls.request(action, values, param)

        retry_num = 1
        while 'success' in result and not result['success'] and retry_num <= max_retries:
            if 'error_code' not in result:
                break

            if cls.can_retry(result.get('error_code')):
                Log.Info('Waiting %ss before retrying request' % retry_sleep)
                time.sleep(retry_sleep)

                Log.Info('Retrying request, retry #%s' % retry_num)
                result = cls.request(action, values, param)
                retry_num += 1
            else:
                Log.Info('Not retrying the request, could be a client error (error with code %s was returned)' %
                         result.get('error_code'))
                break

        return result

    class Account(object):
        @staticmethod
        def test():
            return Trakt.request('account/test')

    class Media(object):
        @staticmethod
        def action(media_type, action, **kwargs):
            if not all([x in kwargs for x in ['duration', 'progress', 'title']]):
                raise ValueError()

            if action == 'scrobble':
                return Trakt.request_retry(media_type + '/' + action, kwargs)

            return Trakt.request(media_type + '/' + action, kwargs)
