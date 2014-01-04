from core.network import request


class PlexBase(object):
    base_url = 'http://localhost:32400'

    @classmethod
    def request(cls, path='/', response_type='xml', raise_exceptions=False, retry=True, timeout=3, **kwargs):
        if not path.startswith('/'):
            path = '/' + path

        response = request(
            cls.base_url + path,
            response_type,

            raise_exceptions=raise_exceptions,

            retry=retry,
            timeout=timeout,

            **kwargs
        )

        return response.data if response else None
