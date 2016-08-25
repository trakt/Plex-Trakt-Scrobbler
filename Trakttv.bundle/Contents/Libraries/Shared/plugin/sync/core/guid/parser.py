from oem.media.movie import MovieMatch
from plugin.core.constants import GUID_SERVICES
from plugin.core.helpers.variable import try_convert
from plugin.modules.core.manager import ModuleManager
from plugin.sync.core.guid.match import GuidMatch

from oem.media.show import EpisodeMatch
from plex_metadata import Guid
import logging

log = logging.getLogger(__name__)


class GuidParser(object):
    @classmethod
    def parse(cls, guid, episode=None):
        media = (
            GuidMatch.Media.Episode
            if episode else GuidMatch.Media.Movie
        )

        # Ensure guid is valid
        if not guid or not guid.valid:
            return GuidMatch(
                media, guid,
                invalid=True
            )

        # Process guid episode identifier overrides
        if episode and len(episode) == 2:
            season_num, episode_num = episode

            if guid.season is not None:
                episode = guid.season, episode_num

        # Process natively supported guid services
        if guid.service in GUID_SERVICES:
            episodes = None

            if episode and len(episode) == 2:
                episodes = [episode]

            return GuidMatch(
                media, guid,
                episodes=episodes,
                supported=True,
                found=True
            )

        # Process episode
        if episode:
            return cls.parse_episode(guid, episode)

        # Process shows + movies
        supported, (service, key) = ModuleManager['mapper'].id(
            guid.service, guid.id,
            resolve_mappings=False
        )

        # Validate match
        if not supported:
            return GuidMatch(media, guid)

        if not service or not key:
            return GuidMatch(media, guid, supported=True)

        # Validate identifier
        if type(key) is list:
            log.info('[%s/%s] - List keys are not supported', guid.service, guid.id)
            return GuidMatch(media, guid, supported=True)

        if type(key) not in [int, str]:
            log.info('[%s/%s] - Unsupported key: %r', guid.service, guid.id, key)
            return GuidMatch(media, guid, supported=True)

        log.debug('[%s/%s] - Mapped to: %s/%s', guid.service, guid.id, service, key)

        # Return movie/show match
        return GuidMatch(
            media, Guid.construct(service, key, matched=True),
            supported=True,
            found=True
        )

    @classmethod
    def parse_episode(cls, guid, (season_num, episode_num)):
        episodes = [(season_num, episode_num)]

        # Map episode to a supported service (via OEM)
        supported, match = ModuleManager['mapper'].map_episode(
            guid, season_num, episode_num,
            resolve_mappings=False
        )

        # Validate match
        if not supported:
            return GuidMatch(
                GuidMatch.Media.Episode, guid,
                episodes=episodes
            )

        if not match or not match.identifiers:
            log.debug('Unable to find mapping for %r S%02dE%02d', guid, season_num, episode_num)
            return GuidMatch(
                GuidMatch.Media.Episode, guid,
                episodes=episodes,
                supported=True
            )

        # Retrieve identifier
        service = match.identifiers.keys()[0]
        key = match.identifiers[service]

        if type(key) is list:
            log.info('[%s/%s] - List keys are not supported', guid.service, guid.id)
            return GuidMatch(
                GuidMatch.Media.Episode, guid,
                episodes=episodes,
                supported=True
            )

        # Cast `key` numbers to integers
        key = try_convert(key, int, key)

        # Validate show identifier
        if type(key) not in [int, str]:
            log.info('[%s/%s] - Unsupported key: %r', guid.service, guid.id, key)
            return GuidMatch(
                GuidMatch.Media.Episode, guid,
                episodes=episodes,
                supported=True
            )

        # Process episode matches
        if isinstance(match, EpisodeMatch):
            # Ensure match doesn't include an absolute number
            if match.absolute_num is not None:
                log.info('[%s/%s] - Episode mappings with absolute numbers are not supported', guid.service, guid.id)
                return GuidMatch(
                    GuidMatch.Media.Episode, guid,
                    episodes=episodes,
                    supported=True
                )

            # Update `episodes` list
            if match.mappings:
                # Use match mappings
                episodes = []

                for mapping in match.mappings:
                    log.debug('[%s/%s] (S%02dE%02d) - Mapped to: %r', guid.service, guid.id, season_num, episode_num, mapping)
                    episodes.append((
                        int(mapping.season),
                        int(mapping.number)
                    ))
            else:
                # Use match identifier
                log.debug('[%s/%s] (S%02dE%02d) - Mapped to: %r', guid.service, guid.id, season_num, episode_num, match)
                episodes = [(
                    int(match.season_num),
                    int(match.episode_num)
                )]

            # Return episode match
            return GuidMatch(
                GuidMatch.Media.Episode, Guid.construct(service, key, matched=True),
                episodes=episodes,
                supported=True,
                found=True
            )

        # Process movie matches
        if isinstance(match, MovieMatch):
            log.debug('[%s/%s] (S%02dE%02d) - Mapped to: %r', guid.service, guid.id, season_num, episode_num, match)

            # Return movie match
            return GuidMatch(
                GuidMatch.Media.Movie, Guid.construct(service, key, matched=True),
                supported=True,
                found=True
            )

        # Unknown value for `match` returned
        log.warn('Unknown match returned: %r', match)
        return GuidMatch(
            GuidMatch.Media.Episode, guid,
            episodes=episodes,
            supported=True
        )
