import logging

log = logging.getLogger(__name__)


class ApiManager(object):
    services = {}

    @classmethod
    def process(cls, key, *args, **kwargs):
        log.debug('Handling API request %r - args: %r, kwargs: %r', key, args, kwargs)

        k_service, k_method = key.rsplit('.', 1)

        # Try find matching service
        service = cls.services.get(k_service)

        if service is None:
            log.warn('Unable to find service: %r', k_service)
            return cls.build_error('unknown.service', 'Unable to find service: %r' % k_service)

        func = getattr(service, k_method, None)

        if func is None:
            log.warn('Unable to find method: %r', k_method)
            return cls.build_error('unknown.method', 'Unable to find method: %r' % k_method)

        try:
            return cls.build_response(func(*args, **kwargs))
        except Exception, ex:
            log.error('Exception raised while handling request %r: %s', key, ex, exc_info=True)
            return cls.build_error('exception', 'Exception raised while handling the request')

    @classmethod
    def register(cls, service):
        key = service.__key__

        if not key:
            log.warn('Service %r has an invalid "__key__" attribute', service)
            return

        cls.services[key] = service

        log.debug('Registered service: %r (%r)', key, service)

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
