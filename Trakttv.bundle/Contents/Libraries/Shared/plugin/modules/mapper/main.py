from oem.media.movie import MovieMatch
from oem.media.show import EpisodeMatch

from plugin.core.environment import Environment
from plugin.core.helpers.variable import try_convert
from plugin.modules.core.base import Module

from oem import OemClient
from oem.media.show.identifier import EpisodeIdentifier
from oem.providers import IncrementalReleaseProvider
from oem_storage_codernitydb.main import CodernityDbStorage
from plex_metadata import Guid
import logging
import os

log = logging.getLogger(__name__)


class Mapper(Module):
    __key__ = 'mapper'

    services = {
        'anidb': ['imdb', 'tvdb']  # Try match against imdb database first
    }

    def __init__(self):
        self._client = None

    def start(self):
        # Construct oem client
        self._client = OemClient(
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

    def map_movie(self, guid, movie):
        # Ensure guid has been parsed
        if type(guid) is str:
            guid = Guid.parse(guid)

        # Try match movie against database
        return self.map(guid.service, guid.id)

    def request_movie(self, guid, movie):
        # Try match movie against database
        supported, match = self.map_movie(guid, movie)

        if not match:
            return supported, None

        # Build request for Trakt.tv
        return supported, self._build_movie_request(match, movie)

    #
    # Shows
    #

    def map_episode(self, guid, season_num, episode_num):
        # Ensure guid has been parsed
        if type(guid) is str:
            guid = Guid.parse(guid)

        # Build episode identifier
        identifier = EpisodeIdentifier(
            season_num=season_num,
            episode_num=episode_num
        )

        # Try match episode against database
        return self.map(guid.service, guid.id, identifier)

    def request_episode(self, guid, episode):
        # Try match episode against database
        supported, match = self.map_episode(guid, episode.season.index, episode.index)

        if not match:
            return supported, None

        # Build request for Trakt.tv
        return supported, self._build_episode_request(match, episode)

    #
    # Helper methods
    #

    def map(self, source, key, identifier=None):
        if source not in self.services:
            return False, None

        for target, service in self._iter_services(source):
            try:
                match = service.map(key, identifier)
            except Exception, ex:
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
            except Exception, ex:
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

    def _build_episode_request(self, match, episode):
        if isinstance(match, MovieMatch):
            # Retrieve mapped identifier
            service = match.identifiers.keys()[0]
            key = try_convert(match.identifiers[service], int, match.identifiers[service])

            if type(key) not in [int, str]:
                log.info('Unsupported key: %r', key)
                return None

            return {
                'movie': {
                    'title': episode.show.title,
                    'year': episode.show.year,

                    'ids': {
                        service: key
                    }
                }
            }

        if isinstance(match, EpisodeMatch):
            if match.absolute_num is not None:
                # TODO support for absolute episode scrobbling
                log.info('Absolute season mappings are not supported yet')
                return None

            if match.season_num is None or match.episode_num is None:
                log.warn('Missing season or episode number in %r', match)
                return None

            # Retrieve mapped identifier
            service = match.identifiers.keys()[0]
            key = try_convert(match.identifiers[service], int, match.identifiers[service])

            if type(key) not in [int, str]:
                log.info('Unsupported key: %r', key)
                return None

            # Build request
            return {
                'show': {
                    'title': episode.show.title,
                    'year': episode.year,

                    'ids': {
                        service: key
                    }
                },
                'episode': {
                    'title': episode.title,

                    'season': match.season_num,
                    'number': match.episode_num
                }
            }

        log.warn('Unknown match returned: %r', match)
        return None
    
    def _build_movie_request(self, match, movie):
        if not isinstance(match, MovieMatch):
            log.warn('Invalid match returned for movie: %r')
            return None

        # Retrieve mapped identifier
        service = movie.identifiers.keys()[0]
        key = try_convert(movie.identifiers[service], int, movie.identifiers[service])

        if type(key) not in [int, str]:
            log.info('Unsupported key: %r', key)
            return None

        # Build request
        return {
            'movie': {
                'title': movie.title,
                'year': movie.year,

                'ids': {
                    service: key
                }
            }
        }

    def _iter_services(self, source):
        if source not in self.services:
            return

        for target in self.services[source]:
            try:
                service = self._client[source].to(target)
            except KeyError:
                log.warn('Unable to find service: %s -> %s', source, target)
                continue
            except Exception, ex:
                log.warn('Unable to retrieve service: %s -> %s - %s', source, target, ex, exc_info=True)
                continue

            yield target, service
