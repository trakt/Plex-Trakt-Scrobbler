from plex.core.helpers import synchronized
from plex.request import PlexRequest

from threading import Condition
import hashlib
import logging
import requests
import socket

log = logging.getLogger(__name__)


class HttpClient(object):
    def __init__(self, client):
        self.client = client

        self.session = requests.Session()
        self.c_path = None

        # Private
        self._lock = Condition()

    @property
    def cache(self):
        return self.client.configuration.get('cache.http')

    def request(self, method, path=None, params=None, query=None, data=None, credentials=None, **kwargs):
        if path is not None and type(path) is not str:
            # Convert `path` to string (excluding NoneType)
            path = str(path)

        if self.c_path and path:
            # Prepend `base_path` to relative `path`s
            if not path.startswith('/'):
                path = self.c_path + '/' + path

        elif self.c_path:
            path = self.c_path
        elif not path:
            path = ''

        # reset request configuration
        self.reset()

        request = PlexRequest(
            self.client,
            method=method,
            path=path,

            params=params,
            query=query,
            data=data,

            credentials=credentials,
            **kwargs
        )

        prepared = request.prepare()

        # Try retrieve cached response
        response = self._cache_lookup(prepared)

        if response:
            return response

        # TODO retrying requests on 502, 503 errors?
        try:
            response = self.session.send(prepared)
        except socket.gaierror as e:
            code, _ = e

            if code != 8:
                raise e

            log.warn('Encountered socket.gaierror (code: 8)')

            response = self._rebuild().send(prepared)

        # Store response in cache
        self._cache_store(prepared, response)

        return response

    def get(self, path=None, params=None, query=None, data=None, **kwargs):
        return self.request('GET', path, params, query, data, **kwargs)

    def put(self, path=None, params=None, query=None, data=None, **kwargs):
        return self.request('PUT', path, params, query, data, **kwargs)

    def post(self, path=None, params=None, query=None, data=None, **kwargs):
        return self.request('POST', path, params, query, data, **kwargs)

    def delete(self, path=None, params=None, query=None, data=None, **kwargs):
        return self.request('DELETE', path, params, query, data, **kwargs)

    def configure(self, path=None):
        self.c_path = path
        return self

    def reset(self):
        self.c_path = None
        return self

    def _rebuild(self):
        log.info('Rebuilding session and connection pools...')

        # Rebuild the connection pool (old pool has stale connections)
        self.session = requests.Session()

        return self.session

    @synchronized
    def _cache_lookup(self, request):
        if self.cache is None:
            return None

        if request.method not in ['GET']:
            return None

        # Retrieve from cache
        return self.cache.get(self._cache_key(request))

    @synchronized
    def _cache_store(self, request, response):
        if self.cache is None:
            return None

        if request.method not in ['GET']:
            return None

        # Store in cache
        self.cache[self._cache_key(request)] = response

    @staticmethod
    def _cache_key(request):
        raw = ','.join([request.method, request.url])

        # Generate MD5 hash of key
        m = hashlib.md5()
        m.update(raw.encode('utf-8'))

        return m.hexdigest()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.reset()
