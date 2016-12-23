from plugin.api.core.exceptions import ApiError
from plugin.preferences import Preferences

from threading import Lock
import logging
import six

log = logging.getLogger(__name__)


class ApiContext(object):
    def __init__(self, method, headers, body):
        self.method = method
        self.headers = headers
        self.body = body

        # Validate token
        self.token = self._validate_token()

    def _validate_token(self):
        token = self.headers.get('X-Channel-Token') if self.headers else None

        if not token:
            return None

        # Validate `token`
        system = ApiManager.get_service('system')

        try:
            return system.validate(token)
        except:
            return None


class ApiManager(object):
    service_classes = {}
    services = {}

    # Call attributes
    lock = Lock()
    context = None

    @classmethod
    def process(cls, method, headers, body, key, *args, **kwargs):
        log.debug('Handling API %s request %r - args: %r, kwargs: %r', method, key, len(args), len(kwargs.keys()))

        if not Preferences.get('api.enabled'):
            log.debug('Unable to process request, API is currently disabled')
            return cls.build_error('disabled', 'Unable to process request, API is currently disabled')

        k_service, k_method = key.rsplit('.', 1)

        # Try find matching service
        service = cls.get_service(k_service)

        if service is None:
            log.warn('Unable to find service: %r', k_service)
            return cls.build_error('unknown.service', 'Unable to find service: %r' % k_service)

        func = getattr(service, k_method, None)

        if func is None:
            log.warn('Unable to find method: %r', k_method)
            return cls.build_error('unknown.method', 'Unable to find method: %r' % k_method)

        # Validate
        meta = getattr(func, '__meta__', {})

        if not meta.get('exposed', False):
            log.warn('Method is not exposed: %r', k_method)
            return cls.build_error('restricted.method', 'Method is not exposed: %r' % k_method)

        # Decode strings in the `args` parameter
        try:
            args = cls.decode(args)
        except Exception as ex:
            return cls.build_error('args.decode_error', 'Unable to decode provided args')

        # Decode strings in the `kwargs` parameter
        try:
            kwargs = cls.decode(kwargs)
        except Exception as ex:
            return cls.build_error('kwargs.decode_error', 'Unable to decode provided kwargs')

        # Execute request handler
        try:
            result = cls.call(method, headers, body, func, args, kwargs)
        except ApiError as ex:
            log.warn('Error returned while handling request %r: %r', key, ex, exc_info=True)
            return cls.build_error('error.%s' % ex.code, ex.message)
        except Exception as ex:
            log.error('Exception raised while handling request %r: %s', key, ex, exc_info=True)
            return cls.build_error('exception', 'Exception raised while handling the request')

        # Build response
        return cls.build_response(result)

    @classmethod
    def call(cls, method, headers, body, func, args, kwargs):
        with cls.lock:
            # Construct context
            cls.context = ApiContext(method, headers, body)

            # Call function
            return func(*args, **kwargs)

    @classmethod
    def register(cls, service):
        key = service.__key__

        if not key:
            log.warn('Service %r has an invalid "__key__" attribute', service)
            return

        cls.service_classes[key] = service

        log.debug('Registered service: %r (%r)', key, service)

    @classmethod
    def get_service(cls, key):
        if key in cls.services:
            # Service already constructed
            return cls.services[key]

        if key not in cls.service_classes:
            # Service doesn't exist
            return None

        # Construct service
        cls.services[key] = cls.service_classes[key](cls)

        return cls.services[key]

    @classmethod
    def decode(cls, data):
        if not data:
            return data

        # Strings
        if isinstance(data, six.string_types):
            try:
                return data.decode('unicode-escape')
            except Exception as ex:
                log.warn('Unable to decode string: %s', ex, exc_info=True)
                return data

        # Collections
        if type(data) is dict:
            return dict([
                (cls.decode(key), cls.decode(value))
                for key, value in data.items()
            ])

        if type(data) is list:
            return [
                cls.decode(value)
                for value in data
            ]

        if type(data) is tuple:
            return tuple([
                cls.decode(value)
                for value in list(data)
            ])

        return data

    @classmethod
    def build_error(cls, code, message=None):
        result = {
            'error': {
                'code': code
            }
        }

        if message:
            result['error']['message'] = message

        return result

    @classmethod
    def build_response(cls, result):
        return {
            'result': result
        }
