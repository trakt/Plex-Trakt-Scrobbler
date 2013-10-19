from core.http import responses
from core.plugin import PLUGIN_VERSION
from core.helpers import all
import socket
import time


TRAKT_URL = 'http://api.trakt.tv/%s/ba5aa61249c02dc5406232da20f6e768f3c82b28%s'


class Trakt(object):
    @staticmethod
    def request(action, values=None, param=''):
        if param != "":
            param = "/" + param
        data_url = TRAKT_URL % (action, param)

        if values is None:
            values = {}

        values['username'] = Prefs['username']
        values['password'] = Hash.SHA1(Prefs['password'])
        values['plugin_version'] = PLUGIN_VERSION
        values['media_center_version'] = Dict['server_version']

        try:
            json_file = HTTP.Request(data_url, data=JSON.StringFromObject(values))
            result = JSON.ObjectFromString(json_file.content)
        except socket.timeout:
            result = {'status': 'failure', 'error_code': 408, 'error': 'timeout'}
        except Ex.HTTPError, e:
            result = {'status': 'failure', 'error_code': e.code, 'error': responses[e.code][1]}
        except Ex.URLError, e:
            result = {'status': 'failure', 'error_code': 0, 'error': e.reason[0]}

        if 'status' in result:
            if result['status'] == 'success':
                if not 'message' in result:
                    if 'inserted' in result:
                        result['message'] = "%s Movies inserted, %s Movies already existed, %s Movies skipped" % (
                            result['inserted'], result['already_exist'], result['skipped']
                        )
                    else:
                        result['message'] = 'Unknown success'

                Log('Trakt responded with: %s' % result['message'])

                return {'status': True, 'message': result['message']}
            elif result['status'] == 'failure':
                Log('Trakt responded with: (%s) %s' % (result.get('error_code'), result.get('error')))

                return {'status': False, 'message': result['error'], 'result': result}

        Log('Return all')
        return {'result': result}

    @classmethod
    def request_retry(cls, action, values=None, param='', max_retries=3, retry_sleep=30):
        result = cls.request(action, values, param)

        retry_num = 1
        while 'status' in result and not result['status'] and retry_num <= max_retries:
            if 'result' not in result:
                break
            if 'error_code' not in result['result']:
                break

            Log('Waiting %ss before retrying request' % retry_sleep)
            time.sleep(retry_sleep)

            if result['result']['error_code'] in [408, 504]:
                Log('Retrying request, retry #%s' % retry_num)
                result = cls.request(action, values, param)
                retry_num += 1
            else:
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
