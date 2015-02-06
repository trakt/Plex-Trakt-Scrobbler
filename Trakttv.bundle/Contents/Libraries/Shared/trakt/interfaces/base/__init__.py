from trakt.core.errors import ERRORS
from trakt.core.exceptions import ServerError, ClientError
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
    def get_data(response, exceptions=False, parse=True):
        if response is None:
            return None

        # Return response, if parse=False
        if not parse:
            return response

        # Parse response, return data
        if response.headers['content-type'].startswith('application/json'):
            # Try parse json response
            try:
                data = response.json()
            except Exception as e:
                log.warning('unable to parse JSON response: %s', e)
                return None
        else:
            log.debug('response returned "%s" content, falling back to raw data', response.headers['content-type'])

            # Fallback to raw content
            data = response.content

        # Check status code, log any errors
        error = False

        if response.status_code < 200 or response.status_code >= 300:
            # Lookup status code in trakt error definitions
            name, desc = ERRORS.get(response.status_code, ("Unknown", "Unknown"))

            log.warning('request failed: %s - "%s" (code: %s)', name, desc, response.status_code)

            if exceptions:
                # Raise an exception (including the response for further processing)
                if response.status_code >= 500:
                    raise ServerError(response)
                else:
                    raise ClientError(response)

            # Set error flag
            error = True

        # Return `None` if we encountered an error, return response data
        if error:
            return None

        return data

    @staticmethod
    def media_mapper(store, media, items, **kwargs):
        if items is None:
            return

        if store is None:
            store = {}

        mapper = MediaMapper(store)

        for item in items:
            result = mapper.process(media, item, **kwargs)

            if result is None:
                log.warn('Unable to map item: %s', item)

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
