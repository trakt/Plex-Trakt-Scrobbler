from trakt.helpers import setdefault
from trakt.media_mapper import MediaMapper

from functools import wraps
import logging

log = logging.getLogger(__name__)


def authenticated(func):
    @wraps(func)
    def wrap(*args, **kwargs):
        if args and isinstance(args[0], Interface):
            interface = args[0]

        return func(*args, **kwargs)

    return wrap


def application(func):
    @wraps(func)
    def wrap(*args, **kwargs):
        if args and isinstance(args[0], Interface):
            interface = args[0]

            setdefault(kwargs, {
                'app_version': interface.client.configuration['app.version'],
                'app_date': interface.client.configuration['app.date']
            }, lambda key, value: value)

        return func(*args, **kwargs)

    return wrap


class Interface(object):
    path = None

    def __init__(self, client):
        self.client = client

    def __getitem__(self, name):
        if hasattr(self, name):
            return getattr(self, name)

        raise ValueError('Unknown action "%s" on %s', name, self)

    @property
    def http(self):
        if not self.client:
            return None

        return self.client.http.configure(self.path)

    @staticmethod
    def get_data(response, catch_errors=True):
        if response is None:
            return None

        try:
            data = response.json()
        except ValueError:
            log.warning('request failure (content: %s)', response.content)
            return None

        # unknown result - no json data returned
        if data is None:
            return None

        error = False

        # unknown result - no response or server error
        if response.status_code >= 500:
            log.warning('request failure (data: %s)', data)
            error = True
        elif type(data) is dict and data.get('status') == 'failure':
            log.warning('request failure (error: "%s")', data.get('error'))
            error = True

        if error and catch_errors:
            return False

        return data

    @staticmethod
    def media_mapper(store, media, items, **kwargs):
        if items is None:
            return

        if store is None:
            store = {}

        mapper = MediaMapper(store)

        for item in items:
            mapper.process(media, item, **kwargs)

        return store


class InterfaceProxy(object):
    def __init__(self, interface, args):
        self.interface = interface
        self.args = list(args)

    def __getattr__(self, name):
        value = getattr(self.interface, name)

        if not hasattr(value, '__call__'):
            return value

        @wraps(value)
        def wrap(*args, **kwargs):
            args = self.args + list(args)

            return value(*args, **kwargs)

        return wrap
