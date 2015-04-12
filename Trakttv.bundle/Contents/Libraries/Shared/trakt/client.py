from trakt.core.configuration import ConfigurationManager
from trakt.core.emitter import Emitter
from trakt.core.http import HttpClient
from trakt.interfaces import construct_map
from trakt.interfaces.base import InterfaceProxy

import logging

__version__ = '2.3.0'

log = logging.getLogger(__name__)


class TraktClient(Emitter):
    base_url = 'https://api-v2launch.trakt.tv'
    version = __version__

    __interfaces = None

    def __init__(self, adapter_kwargs=None):
        # Set parameter defaults
        if adapter_kwargs is None:
            adapter_kwargs = {}

        adapter_kwargs.setdefault('max_retries', 3)

        # Construct
        self.configuration = ConfigurationManager()
        self.http = HttpClient(self, adapter_kwargs)

        self.__interfaces = construct_map(self)

    @property
    def site_url(self):
        url = self.base_url

        schema_end = url.find('://') + 3
        domain_start = url.find('.', schema_end) + 1

        return url[0:schema_end] + url[domain_start:]

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
