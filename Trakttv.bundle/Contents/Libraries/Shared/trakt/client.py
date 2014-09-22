from trakt.core.context import Context
from trakt.core.http import HttpClient
from trakt.interfaces import construct_map
from trakt.interfaces.base import InterfaceProxy

import logging


log = logging.getLogger(__name__)


class TraktClient(object):
    base_url = 'http://api.trakt.tv'
    interfaces = None

    def __init__(self):
        self.client_id = None
        self.client_secret = None

        self.access_token = None

        # Scrobbling parameters
        self.app_version = None
        self.app_date = None

        # Construct
        self.http = HttpClient(self)
        self.interfaces = construct_map(self)

        # Private
        self._context_stack = [Context(self)]

    @property
    def current(self):
        if not self._context_stack:
            return None

        return self._context_stack[-1]

    def context(self, access_token=None):
        return Context(self, access_token)

    def configure(self, **kwargs):
        for key, value in kwargs.items():
            if not hasattr(self, key):
                raise ValueError('Unknown option "%s" specified' % key)

            setattr(self, key, value)

    def __getitem__(self, path):
        parts = path.strip('/').split('/')

        cur = self.interfaces

        while parts and type(cur) is dict:
            key = parts.pop(0)

            if key not in cur:
                return None

            cur = cur[key]

        if type(cur) is dict:
            cur = cur.get(None)

        if parts:
            return InterfaceProxy(cur, parts)

        return cur
