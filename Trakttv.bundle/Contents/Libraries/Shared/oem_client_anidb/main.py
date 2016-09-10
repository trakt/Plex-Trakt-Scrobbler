from oem.core.services.base import Service
from oem.media.movie import MovieMapper
from oem.media.show import ShowMapper
from oem_client_anidb.constants import DATABASES, PACKAGES, SERVICES
from oem_framework.models import Movie, Show

import logging

log = logging.getLogger(__name__)


class AniDbService(Service):
    __key__ = 'anidb'

    __databases__ = DATABASES
    __packages__ = PACKAGES

    __services__ = SERVICES

    def __init__(self, client, source, target, formats=None):
        super(AniDbService, self).__init__(client, source, target, formats)

        # Construct media mappers
        self._movie_mapper = MovieMapper(self)
        self._show_mapper = ShowMapper(self)

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

    def map(self, key, identifier=None, resolve_mappings=True):
        # Retrieve item
        item = self.get(key)

        if item is None:
            return None

        if isinstance(item, Movie):
            match = self._movie_mapper.match(
                item, identifier,
                resolve_mappings=resolve_mappings
            )
        elif isinstance(item, Show):
            match = self._show_mapper.match(
                item, identifier,
                resolve_mappings=resolve_mappings
            )
        else:
            raise ValueError('Unknown item: %r' % item)

        # Validate match
        if not match or not match.valid:
            if identifier:
                log.warn('[%s/%s] Unable to find mapping for %%r' % (self.source_key, key), identifier, extra={
                    'event': {
                        'module': __name__,
                        'name': 'map.missing_mapping',
                        'key': (self.source_key, key, identifier)
                    }
                })
            else:
                log.warn('[%s/%s] Unable to find mapping' % (self.source_key, key), extra={
                    'event': {
                        'module': __name__,
                        'name': 'map.missing_mapping',
                        'key': (self.source_key, key)
                    }
                })

            return None

        return match

    def titles(self, key):
        pass

    def __getitem__(self, key):
        pass
