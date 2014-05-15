from core.network import request


class PlexBase(object):
    base_url = 'http://127.0.0.1:32400'

    @classmethod
    def request(cls, path='/', response_type='xml', raise_exceptions=False,
                retry=True, timeout=3, max_retries=3, retry_sleep=5, **kwargs):
        if not path.startswith('/'):
            path = '/' + path

        response = request(
            cls.base_url + path,
            response_type,

            raise_exceptions=raise_exceptions,

            retry=retry,
            timeout=timeout,
            max_retries=max_retries,
            retry_sleep=retry_sleep,

            **kwargs
        )

        return response.data if response else None
