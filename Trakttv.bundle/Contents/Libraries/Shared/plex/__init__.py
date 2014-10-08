from plex.client import PlexClient
from plex.helpers import has_attribute

__version__ = '0.5.0-develop'


class PlexMeta(type):
    @property
    def client(cls):
        if cls._client is None:
            cls.construct()

        return cls._client

    def __getattr__(self, name):
        if has_attribute(self, name):
            return super(PlexMeta, self).__getattribute__(name)

        if self.client is None:
            self.construct()

        return getattr(self.client, name)

    def __setattr__(self, name, value):
        if has_attribute(self, name):
            return super(PlexMeta, self).__setattr__(name, value)

        if self.client is None:
            self.construct()

        setattr(self.client, name, value)

    def __getitem__(self, key):
        if self.client is None:
            self.construct()

        return self.client[key]


class Plex(object):
    __metaclass__ = PlexMeta

    _client = None

    @classmethod
    def construct(cls):
        cls._client = PlexClient()
