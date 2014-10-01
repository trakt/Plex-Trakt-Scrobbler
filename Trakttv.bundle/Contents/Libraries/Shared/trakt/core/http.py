from trakt.core.context import ContextStack
from trakt.core.request import TraktRequest

import logging
import requests
import socket

log = logging.getLogger(__name__)


class HttpClient(object):
    def __init__(self, client):
        self.client = client

        self.configuration = ContextStack()
        self.session = requests.Session()

    def configure(self, path=None):
        self.configuration.push(base_path=path)

        return self

    def request(self, method, path=None, params=None, data=None, **kwargs):
        ctx = self.configuration.pop()

        if ctx.base_path and path:
            path = ctx.base_path + '/' + path
        elif ctx.base_path:
            path = ctx.base_path

        request = TraktRequest(
            self.client,
            method=method,
            path=path,
            params=params,
            data=data,

            **kwargs
        )

        prepared = request.prepare()

        # TODO retrying requests on 502, 503 errors?
        try:
            return self.session.send(prepared)
        except socket.gaierror, e:
            code, _ = e

            if code != 8:
                raise e

            log.warn('Encountered socket.gaierror (code: 8)')

            return self._rebuild().send(prepared)

    def get(self, path=None, params=None, data=None, **kwargs):
        return self.request('GET', path, params, data, **kwargs)

    def post(self, path=None, params=None, data=None, **kwargs):
        return self.request('POST', path, params, data, **kwargs)

    def delete(self, path=None, params=None, data=None, **kwargs):
        return self.request('DELETE', path, params, data, **kwargs)

    def _rebuild(self):
        log.info('Rebuilding session and connection pools...')

        # Rebuild the connection pool (old pool has stale connections)
        self.session = requests.Session()

        return self.session
