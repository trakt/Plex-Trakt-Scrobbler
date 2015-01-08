from trakt.core.configuration import ConfigurationManager
from trakt.core.http import HttpClient
from trakt.interfaces import construct_map
from trakt.interfaces.base import InterfaceProxy

import logging

__version__ = '2.0.8'

log = logging.getLogger(__name__)


class TraktClient(object):
    base_url = 'https://api.trakt.tv'
    version = __version__

    __interfaces = None

    def __init__(self):
        # Construct
        self.http = HttpClient(self)
        self.configuration = ConfigurationManager()

        self.__interfaces = construct_map(self)

    def __getitem__(self, path):
        parts = path.strip('/').split('/')

        cur = self.__interfaces

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
