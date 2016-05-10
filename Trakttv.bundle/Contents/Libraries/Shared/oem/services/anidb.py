from oem.media.show.mapper import ShowMapper
from oem.services.core.base import Service

import logging

log = logging.getLogger(__name__)


class AniDbService(Service):
    __services__ = {
        'anidb':    ['imdb', 'tvdb'],
        'imdb':     ['anidb'],
        'tvdb':     ['anidb']
    }

    def __init__(self, client, source, target, formats=None):
        super(AniDbService, self).__init__(client, source, target, formats)

        self.mapper = ShowMapper(self)

    def get(self, key, default=None):
        # Retrieve item metadata
        metadata = self.get_metadata(key)

        if metadata is None:
            return default

        # Ensure item is available
        if not self.fetch(key, metadata):
            return default

        # Retrieve item from disk
        return metadata.get()

    def get_metadata(self, key, default=None):
        # Ensure service is loaded
        if not self.load():
            return default

        # Retrieve item metadata
        try:
            return self._collection[key]
        except KeyError:
            return default

    def map(self, key, identifier):
        # Retrieve item
        item = self.get(key)

        if item is None:
            return None

        # Map episode
        return self.mapper.match(item, identifier)

    def titles(self, key):
        pass

    def __getitem__(self, key):
        pass
