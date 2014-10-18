from trakt.helpers import parse_credentials, setdefault
from trakt.media_mapper import MediaMapper

from functools import wraps
import logging

log = logging.getLogger(__name__)


def authenticated(func):
    @wraps(func)
    def wrap(*args, **kwargs):
        if args and isinstance(args[0], Interface):
            interface = args[0]

            if 'credentials' not in kwargs:
                kwargs['credentials'] = interface.client.credentials
            else:
                kwargs['credentials'] = parse_credentials(kwargs['credentials'])

        return func(*args, **kwargs)

    return wrap


def media_center(func):
    @wraps(func)
    def wrap(*args, **kwargs):
        if args and isinstance(args[0], Interface):
            interface = args[0]

            setdefault(kwargs, {
                'plugin_version': interface.client.plugin_version,

                'media_center_version': interface.client.media_center_version,
                'media_center_date': interface.client.media_center_date
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

    def request(self, path, params=None, data=None, credentials=None, **kwargs):
        return self.client.request(
            '%s/%s' % (self.path, path),
            params, data,
            credentials,
            **kwargs
        )

    @authenticated
    def action(self, action, data=None, credentials=None, **kwargs):
        if data:
            # Merge kwargs (extra request parameters)
            data.update(kwargs)

            # Strip any parameters with 'None' values
            data = dict([
                (key, value)
                for key, value in data.items()
                if value is not None
            ])

        if not self.validate_action(action, data):
            return None

        response = self.request(
            action, data=data,
            credentials=credentials
        )

        return self.get_data(response, catch_errors=False)

    @classmethod
    def validate_action(cls, action, data):
        return True

    @staticmethod
    def get_data(response, catch_errors=True):
        # unknown result - no response or server error
        if response is None or response.status_code >= 500:
            return None

        data = response.json()

        # unknown result - no json data returned
        if data is None:
            return None

        # invalid result - request failure
        if type(data) is dict and data.get('status') == 'failure':
            log.warning('request failure (error: "%s")', data.get('error'))

            if catch_errors:
                return False

        return data

    @staticmethod
    def data_requirements(data, *args):
        for keys in args:
            if type(keys) is not tuple:
                keys = (keys,)

            values = [data.get(key) for key in keys]

            if all(values):
                return True

        log.warn("Request %s doesn't match data requirements %s, one group of parameters is required.", data, args)
        return False

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
