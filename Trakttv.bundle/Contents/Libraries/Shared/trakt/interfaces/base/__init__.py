from trakt.core.errors import ERRORS
from trakt.core.exceptions import ServerError, ClientError
from trakt.core.helpers import try_convert
from trakt.core.pagination import PaginationIterator
from trakt.helpers import setdefault

from functools import wraps
from six.moves.urllib.parse import urlparse
import logging
import warnings

log = logging.getLogger(__name__)


def authenticated(func):
    @wraps(func)
    def wrap(*args, **kwargs):
        kwargs['authenticated'] = True

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

        raise ValueError('Unknown action "%s" on %s' % (name, self))

    @property
    def http(self):
        if not self.client:
            return None

        return self.client.http.configure(self.path)

    def get_data(self, response, exceptions=False, pagination=False, parse=True):
        if response is None:
            return None

        # Return response, if parse=False
        if not parse:
            return response

        # Check status code, log any errors
        error = False

        if response.status_code < 200 or response.status_code >= 300:
            # Lookup status code in trakt error definitions
            name, desc = ERRORS.get(response.status_code, ("Unknown", "Unknown"))

            # Display warning (with extra debug information)
            method = response.request.method
            path = urlparse(response.request.url).path
            code = response.status_code

            log.warn('Request failed: "%s %s" - %s: "%%s" (%%s)' % (method, path, code), desc, name, extra={
                'data': {
                    'http.headers': {
                        'cf-ray': response.headers.get('cf-ray'),
                        'X-Request-Id': response.headers.get('X-Request-Id'),
                        'X-Runtime': response.headers.get('X-Runtime')
                    }
                }
            })

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

        # Check for pagination response
        page_count = try_convert(response.headers.get('x-pagination-page-count'), int)

        if page_count and page_count > 1:
            if pagination:
                return PaginationIterator(self.client, response)

            warnings.warn('Unhandled pagination response, more pages can be returned with `pagination=True`', stacklevel=3)

        # Parse response, return data
        content_type = response.headers.get('content-type')

        if content_type and content_type.startswith('application/json'):
            # Try parse json response
            try:
                data = response.json()
            except Exception as e:
                log.warning('unable to parse JSON response: %s', e)
                return None
        else:
            log.debug('response returned content-type: %r, falling back to raw data', content_type)

            # Fallback to raw content
            data = response.content

        return data


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
