from trakt.core.configuration import DEFAULT_HTTP_RETRY, DEFAULT_HTTP_MAX_RETRIES, DEFAULT_HTTP_TIMEOUT, \
    DEFAULT_HTTP_RETRY_SLEEP
from trakt.core.context_stack import ContextStack
from trakt.core.helpers import synchronized
from trakt.core.request import TraktRequest

from requests.adapters import HTTPAdapter, DEFAULT_POOLBLOCK
from threading import Lock
import calendar
import datetime
import logging
import requests
import socket
import time

try:
    import ssl
except ImportError:
    ssl = None

log = logging.getLogger(__name__)


class HttpClient(object):
    def __init__(self, client, adapter_kwargs=None):
        self.client = client
        self.adapter_kwargs = adapter_kwargs or {}

        # Build client
        self.configuration = ContextStack()
        self.session = None

        self._proxies = {}
        self._validate_oauth_lock = Lock()

        self.rebuild()

    @property
    def proxies(self):
        if self.session and self.session.proxies:
            return self.session.proxies

        return self._proxies

    @proxies.setter
    def proxies(self, proxies):
        if self.session:
            self.session.proxies = proxies

        self._proxies = proxies

    def configure(self, path=None):
        self.configuration.push(base_path=path)

        return self

    def request(self, method, path=None, params=None, data=None, query=None, authenticated=False, **kwargs):
        # retrieve configuration
        ctx = self.configuration.pop()

        retry = self.client.configuration.get('http.retry', DEFAULT_HTTP_RETRY)
        max_retries = self.client.configuration.get('http.max_retries', DEFAULT_HTTP_MAX_RETRIES)
        retry_sleep = self.client.configuration.get('http.retry_sleep', DEFAULT_HTTP_RETRY_SLEEP)
        timeout = self.client.configuration.get('http.timeout', DEFAULT_HTTP_TIMEOUT)

        # build request
        if ctx.base_path and path:
            # Prepend `base_path` to relative `path`s
            if not path.startswith('/'):
                path = ctx.base_path + '/' + path

        elif ctx.base_path:
            path = ctx.base_path

        request = TraktRequest(
            self.client,
            method=method,

            path=path,
            params=params,

            data=data,
            query=query,

            authenticated=authenticated,
            **kwargs
        )

        # Validate authentication details (OAuth)
        if authenticated and not self.validate():
            return None

        # Prepare request
        prepared = request.prepare()

        response = None

        for i in range(max_retries + 1):
            if i > 0:
                log.warn('Retry # %s', i)

            # Send request
            try:
                response = self.session.send(prepared, timeout=timeout)
            except socket.gaierror as e:
                code, _ = e

                if code != 8:
                    raise e

                log.warn('Encountered socket.gaierror (code: 8)')

                response = self.rebuild().send(prepared, timeout=timeout)

            # Retry requests on errors >= 500 (when enabled)
            if not retry or response.status_code < 500:
                break

            log.warn('Continue retry since status is %s, waiting %s seconds', response.status_code, retry_sleep)
            time.sleep(retry_sleep)

        return response

    def delete(self, path=None, params=None, data=None, **kwargs):
        return self.request('DELETE', path, params, data, **kwargs)

    def get(self, path=None, params=None, data=None, **kwargs):
        return self.request('GET', path, params, data, **kwargs)

    def post(self, path=None, params=None, data=None, **kwargs):
        return self.request('POST', path, params, data, **kwargs)

    def put(self, path=None, params=None, data=None, **kwargs):
        return self.request('PUT', path, params, data, **kwargs)

    def rebuild(self):
        if self.session:
            log.info('Rebuilding session and connection pools...')

        # Build the connection pool
        self.session = requests.Session()
        self.session.proxies = self.proxies

        # Mount adapters
        self.session.mount('http://', HTTPAdapter(**self.adapter_kwargs))

        if ssl is not None:
            self.session.mount('https://', HTTPSAdapter(ssl_version=ssl.PROTOCOL_TLSv1, **self.adapter_kwargs))
        else:
            log.warn('"ssl" module is not available, unable to change "ssl_version"')
            self.session.mount('https://', HTTPSAdapter(**self.adapter_kwargs))

        return self.session

    def validate(self):
        config = self.client.configuration

        # xAuth
        if config['auth.login'] and config['auth.token']:
            return True

        # OAuth
        if config['oauth.token']:
            # Validate OAuth token, refresh if needed
            return self._validate_oauth()

        return False

    @synchronized(lambda self: self._validate_oauth_lock)
    def _validate_oauth(self):
        config = self.client.configuration

        if config['oauth.created_at'] is None or config['oauth.expires_in'] is None:
            log.debug('OAuth - Missing "created_at" or "expires_in" parameter, '
                      'unable to determine if token is still valid')
            return True

        current = calendar.timegm(datetime.datetime.utcnow().utctimetuple())
        expires_at = config['oauth.created_at'] + config['oauth.expires_in'] - (48 * 60 * 60)

        if current < expires_at:
            return True

        if not config['oauth.refresh']:
            log.warn('OAuth - Unable to refresh expired token (token refreshing hasn\'t been enabled)')
            return False

        if not config['oauth.refresh_token']:
            log.warn('OAuth - Unable to refresh expired token ("refresh_token" is parameter is missing)')
            return False

        # Refresh token
        response = self.client['oauth'].token_refresh(config['oauth.refresh_token'], 'urn:ietf:wg:oauth:2.0:oob')

        if not response:
            log.warn('OAuth - Unable to refresh expired token (error occurred while trying to refresh the token)')
            return False

        # Update current configuration
        config.current.oauth.from_response(response)

        # Fire refresh event
        self.client.emit('oauth.token_refreshed', response)
        return True


class HTTPSAdapter(HTTPAdapter):
    def __init__(self, ssl_version=None, *args, **kwargs):
        self._ssl_version = ssl_version

        super(HTTPSAdapter, self).__init__(*args, **kwargs)

    def init_poolmanager(self, connections, maxsize, block=DEFAULT_POOLBLOCK, **pool_kwargs):
        pool_kwargs['ssl_version'] = self._ssl_version

        return super(HTTPSAdapter, self).init_poolmanager(
            connections, maxsize, block,
            **pool_kwargs
        )
