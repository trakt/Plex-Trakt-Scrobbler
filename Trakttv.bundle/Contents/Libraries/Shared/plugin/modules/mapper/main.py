from oem.media.movie import MovieMatch
from oem.media.show import EpisodeMatch

from plugin.core.environment import Environment
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

    def movie_match(self, guid, movie):
        # Ensure guid has been parsed
        if type(guid) is str:
            guid = Guid.parse(guid)

        # Try match movie against database
        return self.match(guid.service, guid.id)

    def movie_request(self, guid, movie):
        # Try match movie against database
        match = self.movie_match(guid, movie)

        if not match:
            return None

        # Build request for Trakt.tv
        return self._build_movie_request(match, movie)

    #
    # Shows
    #

    def episode_match(self, guid, episode):
        # Ensure guid has been parsed
        if type(guid) is str:
            guid = Guid.parse(guid)

        # Build episode identifier
        identifier = EpisodeIdentifier(
            season_num=episode.season.index,
            episode_num=episode.index
        )

        # Try match episode against database
        return self.match(guid.service, guid.id, identifier)

    def episode_request(self, guid, episode):
        # Try match episode against database
        match = self.episode_match(guid, episode)

        if not match:
            return None

        # Build request for Trakt.tv
        return self._build_episode_request(match, episode)

    #
    # Helper methods
    #

    def match(self, source, key, identifier=None):
        if source not in self.services:
            log.info('Ignoring unsupported source: %r', source)
            return None

        for target in self.services[source]:
            try:
                service = self._client[source].to(target)
            except KeyError:
                log.warn('Unable to find service: %s -> %s', source, target)
                continue
            except Exception, ex:
                log.warn('Unable to retrieve service: %s -> %s - %s', source, target, ex, exc_info=True)
                continue

            try:
                result = service.map(key, identifier)
            except Exception, ex:
                log.warn('Unable to retrieve mapping for %r (%s -> %s) - %s', key, source, target, ex, exc_info=True)
                continue

            if result:
                return result

        log.warn('Unable to find mapping for %s: %r (S%02dE%02d)', source, key, identifier.season_num, identifier.episode_num)
        return None

    def _build_episode_request(self, match, episode):
        if isinstance(match, MovieMatch):
            return {
                'movie': {
                    'title': episode.show.title,
                    'year': episode.show.year,

                    'ids': match.identifiers
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

            return {
                'show': {
                    'title': episode.show.title,
                    'year': episode.year,

                    'ids': match.identifiers
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

        return {
            'movie': {
                'title': movie.title,
                'year': movie.year,

                'ids': match.identifiers
            }
        }
