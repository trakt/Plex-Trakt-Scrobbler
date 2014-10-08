from plex.client import PlexClient
from plex.helpers import has_attribute

__version__ = '0.5.0-develop'


class PlexMeta(type):
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

    client = None

    @classmethod
    def construct(cls):
        cls.client = PlexClient()
