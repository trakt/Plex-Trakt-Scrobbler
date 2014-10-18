from plex.core.configuration import ConfigurationManager
from plex.core.http import HttpClient
from plex.interfaces import construct_map
from plex.interfaces.core.base import InterfaceProxy
from plex.objects.core.manager import ObjectManager

import logging
import socket

log = logging.getLogger(__name__)


class PlexClient(object):
    __interfaces = None

    def __init__(self):
        # Construct interfaces
        self.http = HttpClient(self)
        self.configuration = ConfigurationManager()

        self.__interfaces = construct_map(self)

        # Discover modules
        ObjectManager.construct()

    @property
    def base_url(self):
        host = self.configuration.get('server.host', '127.0.0.1')
        port = self.configuration.get('server.port', 32400)

        return 'http://%s:%s' % (host, port)

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

    def __getattr__(self, name):
        interface = self.__interfaces.get(None)

        if not interface:
            raise Exception("Root interface not found")

        return getattr(interface, name)
