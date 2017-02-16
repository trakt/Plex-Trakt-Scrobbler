from plugin.core.environment import Environment
from plugin.core.helpers.variable import try_convert
from plugin.modules.core.base import Module
from plugin.modules.mapper.handlers.hama import HamaMapper

from oem import OemClient, AbsoluteNumberRequiredError
from oem.media.movie import MovieMatch
from oem.media.show import EpisodeIdentifier, EpisodeMatch
from oem_client_provider_release import IncrementalReleaseProvider
from oem_storage_codernitydb.main import CodernityDbStorage
from plex_metadata import Guid
import logging
import os

log = logging.getLogger(__name__)


class Mapper(Module):
    __key__ = 'mapper'

    services = {
        'anidb': [
            # Prefer movies
            'tmdb:movie', 'imdb',

            # Fallback to shows
            'tvdb'
        ],
        'tvdb': [
            'anidb'
        ]
    }

    def __init__(self):
        self._client = None

        # Construct handlers
        self._handlers = {
            'hama': HamaMapper(self)
        }

    def start(self):
        # Construct oem client
        self._client = OemClient(
            services=[
                'anidb'
            ],
            provider=IncrementalReleaseProvider(
                fmt='minimize+msgpack',
                storage=CodernityDbStorage(os.path.join(
                    Environment.path.plugin_caches,
                    'oem'
                ))
            )
        )

    #
    # Movie
    #

    def map_movie(self, guid, movie, progress=None, part=None, resolve_mappings=True):
        # Ensure guid has been parsed
        if type(guid) is str:
            guid = Guid.parse(guid, strict=True)

        # Ensure parsed guid is valid
        if not guid or not isinstance(guid, Guid) or not guid.valid:
            return False, None

        # Try match movie against database
        return self.map(
            guid.service, guid.id,
            resolve_mappings=resolve_mappings
        )

    def request_movie(self, guid, movie, progress=None, part=None):
        # Try match movie against database
        supported, match = self.map_movie(
            guid, movie,

            progress=progress,
            part=part
        )

        if not match:
            return supported, None

        if supported:
            log.debug('[%s/%s] - Mapped to: %r', guid.service, guid.id, match)

        # Build request for Trakt.tv
        return supported, self._build_request(match, movie)

    #
    # Shows
    #

    def map_episode(self, guid, season_num, episode_num, progress=None, part=None, resolve_mappings=True):
        # Ensure guid has been parsed
        if type(guid) is str:
            guid = Guid.parse(guid, strict=True)

        # Ensure parsed guid is valid
        if not guid or not isinstance(guid, Guid) or not guid.valid:
            return False, None

        # Build episode identifier
        identifier = EpisodeIdentifier(
            season_num=season_num,
            episode_num=episode_num,

            progress=progress,
            part=part
        )

        # Try match episode against database
        return self.map(
            guid.service, guid.id, identifier,
            resolve_mappings=resolve_mappings
        )

    def request_episode(self, guid, episode, progress=None, part=None):
        season_num = episode.season.index
        episode_num = episode.index

        # Process guid episode identifier overrides
        if guid.season is not None:
            season_num = guid.season

        # Try match episode against database
        supported, match = self.map_episode(
            guid,
            season_num,
            episode_num,

            progress=progress,
            part=part
        )

        if not match:
            return supported, None

        if supported:
            log.debug('[%s/%s] - Mapped to: %r', guid.service, guid.id, match)

        # Build request for Trakt.tv
        return supported, self._build_request(match, episode.show, episode)

    #
    # Helper methods
    #

    def id(self, source, key, identifier=None, resolve_mappings=True):
        # Retrieve mapping from database
        supported, match = self.map(
            source, key,
            identifier=identifier,
            resolve_mappings=resolve_mappings
        )

        if not supported:
            return False, (None, None)

        if not match or not match.valid:
            return True, (None, None)

        # Find valid identifier
        for id_service, id_key in match.identifiers.items():
            if id_service == source:
                continue

            # Strip media from identifier key
            id_service_parts = id_service.split(':', 1)

            if len(id_service_parts) == 2:
                id_service, _ = tuple(id_service_parts)

            if id_service in ['tvdb', 'tmdb', 'tvrage']:
                id_key = try_convert(id_key, int, id_key)

            return True, (id_service, id_key)

        log.info('[%s/%s] - Unable to find valid identifier in %r', source, key, match.identiifers)
        return True, (None, None)

    def map(self, source, key, identifier=None, resolve_mappings=True, use_handlers=True):
        if source not in self.services:
            if use_handlers:
                # Try find handler to map the identifier
                return self._map_handler(
                    source, key,
                    identifier=identifier,
                    resolve_mappings=resolve_mappings
                )

            return False, None

        # Iterate through available services until we find a match
        for target, service in self._iter_services(source):
            try:
                match = service.map(
                    key, identifier,
                    resolve_mappings=resolve_mappings
                )
            except AbsoluteNumberRequiredError:
                log.info('Unable to retrieve mapping for %r (%s -> %s) - Absolute mappings are not supported yet', key, source, target)
                continue
            except Exception as ex:
                log.warn('Unable to retrieve mapping for %r (%s -> %s) - %s', key, source, target, ex, exc_info=True)
                continue

            if match:
                return True, match

        return True, None

    def match(self, source, key):
        if source not in self.services:
            return False, None

        for target, service in self._iter_services(source):
            try:
                result = service.get(key)
            except Exception as ex:
                log.warn('Unable to retrieve item for %r (%s -> %s) - %s', key, source, target, ex, exc_info=True)
                continue

            if result:
                return True, result

        log.warn('Unable to find item for %s: %r' % (source, key), extra={
            'event': {
                'module': __name__,
                'name': 'match.missing_item',
                'key': (source, key)
            }
        })
        return True, None

    def _build_request(self, match, item, episode=None):
        if not match:
            log.warn('Invalid value provided for "match" parameter')
            return None

        if not item:
            log.warn('Invalid value provided for "item" parameter')
            return None

        # Retrieve identifier
        id_service = match.identifiers.keys()[0]
        id_key = try_convert(match.identifiers[id_service], int, match.identifiers[id_service])

        if type(id_key) not in [int, str]:
            log.info('Unsupported key: %r', id_key)
            return None

        # Determine media type
        if isinstance(match, MovieMatch):
            media = 'movie'
        elif isinstance(match, EpisodeMatch):
            media = 'show'
        else:
            log.warn('Unknown match: %r', match)
            return None

        # Strip media from identifier key
        id_service_parts = id_service.split(':', 1)

        if len(id_service_parts) == 2:
            id_service, id_media = tuple(id_service_parts)
        else:
            id_media = None

        if id_media and id_media != media:
            log.warn('Identifier mismatch, [%s: %r] doesn\'t match %r', id_service, id_key, media)
            return None

        # Build request
        request = {
            media: {
                'title': item.title,

                'ids': {
                    id_service: id_key
                }
            }
        }

        if item.year:
            request[media]['year'] = item.year
        elif episode and episode.year:
            request[media]['year'] = episode.year
        else:
            log.warn('Missing "year" parameter on %r', item)

        # Add episode parameters
        if isinstance(match, EpisodeMatch):
            if match.absolute_num is not None:
                log.info('Absolute mappings are not supported')
                return None

            if match.season_num is None or match.episode_num is None:
                log.warn('Missing season or episode number in %r', match)
                return None

            request['episode'] = {
                'season': match.season_num,
                'number': match.episode_num
            }

            if episode:
                request['episode']['title'] = episode.title

        return request

    def _iter_services(self, source):
        if source not in self.services:
            return

        for target in self.services[source]:
            try:
                service = self._client[source].to(target)
            except KeyError:
                log.warn('Unable to find service: %s -> %s', source, target)
                continue
            except Exception as ex:
                log.warn('Unable to retrieve service: %s -> %s - %s', source, target, ex, exc_info=True)
                continue

            yield target, service

    def _map_handler(self, source, key, identifier=None, resolve_mappings=True):
        if not source:
            return False, None

        parts = source.split('/', 1)

        if len(parts) != 2:
            return False, None

        # Try find a matching handler
        handler, source = tuple(parts)

        if handler not in self._handlers:
            return False, None

        # Map identifier with handler
        return self._handlers[handler].map(
            source, key,
            identifier=identifier,
            resolve_mappings=resolve_mappings
        )
