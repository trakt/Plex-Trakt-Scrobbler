from oem.core.exceptions import AbsoluteNumberRequiredError
from oem.media.show.identifier import EpisodeIdentifier
from oem.media.show.match import EpisodeMatch
from oem_framework.core.helpers import try_convert

from copy import deepcopy
import logging

log = logging.getLogger(__name__)


class ShowMapper(object):
    def __init__(self, service):
        self._service = service

    def match(self, show, identifier):
        if identifier is None or not isinstance(identifier, EpisodeIdentifier) or not identifier.valid:
            raise ValueError('Invalid value provided for "identifier" parameter')

        # Show
        best = self._match_show(show, identifier)

        # Season
        season, result = self._match_season(show, identifier)

        if result:
            best = result

        if season:
            # Episode
            result = self._match_episode(show, season, identifier)

            if result:
                best = result

        # Return best result
        return best

    def _match_show(self, show, identifier):
        # Retrieve "default_season" parameter
        default_season = None

        if 'default_season' in show.parameters:
            default_season = show.parameters['default_season']

            if default_season != 'a':
                # Cast season number to an integer
                default_season = try_convert(default_season, int)

                if default_season is None:
                    log.warn(
                        'Invalid value provided for the "default_season" parameter: %r',
                        show.parameters['default_season']
                    )
                    return None

        # Retrieve season number
        season_num = identifier.season_num

        if season_num is None or default_season is None or default_season == 'a':
            season_num = default_season
        elif season_num > 0:
            season_num = default_season + (season_num - 1)

        # Retrieve episode number
        episode_num = identifier.episode_num

        if 'episode_offset' in show.parameters:
            episode_num += int(show.parameters['episode_offset'])

        # Build episode match
        if season_num != 'a':
            match = EpisodeMatch(
                self._get_identifiers(show),
                season_num=season_num,
                episode_num=episode_num
            )
        else:
            if identifier.absolute_num is None:
                raise AbsoluteNumberRequiredError('Unable to match %r, an absolute number is required' % identifier)

            match = EpisodeMatch(
                self._get_identifiers(show),
                absolute_num=identifier.absolute_num
            )

        if not match.valid:
            return None

        return match

    def _match_season(self, show, identifier):
        # Try retrieve matching season
        season = show.seasons.get(str(identifier.season_num)) or show.seasons.get('a')

        if not season:
            return None, None

        if season.number == 'a':
            if identifier.absolute_num is None:
                raise AbsoluteNumberRequiredError('Unable to match %r, an absolute number is required' % identifier)

            return season, EpisodeMatch(
                self._get_identifiers(show, season),
                absolute_num=identifier.absolute_num
            )

        # Look for matching season mapping
        for season_mapping in season.mappings:
            if not (season_mapping.start <= identifier.episode_num <= season_mapping.end):
                continue

            return season, EpisodeMatch(
                self._get_identifiers(show, season),
                int(season_mapping.season),
                identifier.episode_num + season_mapping.offset
            )

        # Retrieve "default_season" parameter
        default_season = None

        if 'default_season' in season.parameters:
            default_season = season.parameters['default_season']

            if default_season != 'a':
                # Cast season number to an integer
                default_season = try_convert(default_season, int)

                if default_season is None:
                    log.warn(
                        'Invalid value provided for the "default_season" parameter: %r',
                        season.parameters['default_season']
                    )
                    return season, None

        # Retrieve season number
        season_num = identifier.season_num

        if season.identifiers:
            season_num = 1

        if default_season is not None:
            season_num = default_season

        # Retrieve episode number
        episode_num = identifier.episode_num

        # Apply episode offset
        episode_offset = self._get_parameter('episode_offset', show, season)

        if episode_offset is not None:
            episode_num += int(episode_offset)

        # Build season match
        match = EpisodeMatch(
            self._get_identifiers(show, season),
            season_num=season_num,
            episode_num=episode_num
        )

        if not match.valid:
            return season, None

        return season, match

    def _match_episode(self, show, season, identifier):
        episode = season.episodes.get(str(identifier.episode_num))

        if not episode:
            return None

        for episode_mapping in episode.mappings:
            # Parse timeline attributes
            if episode_mapping.timeline and 'source' in episode_mapping.timeline:
                if identifier.progress is None:
                    raise ValueError('Missing required parameter "progress"')

                timeline_source = episode_mapping.timeline['source']

                if not (timeline_source.start <= identifier.progress <= timeline_source.end):
                    # Ignore `episode_mapping`
                    continue

            # Parse mapping attributes
            try:
                season_num = int(episode_mapping.season)
            except:
                continue

            try:
                episode_num = int(episode_mapping.number)
            except:
                continue

            # Return episode match
            match = EpisodeMatch(
                self._get_identifiers(show, season, episode),
                season_num=season_num,
                episode_num=episode_num
            )

            if not match.valid:
                return None

            return match

        return None

    def _get_identifiers(self, show, season=None, episode=None):
        # Retrieve identifiers from objects
        if show and season and episode:
            identifiers = episode.identifiers or season.identifiers or show.identifiers
        elif show and season:
            identifiers = season.identifiers or show.identifiers
        else:
            identifiers = show.identifiers

        # Copy identifiers
        if identifiers:
            identifiers = deepcopy(identifiers)
        else:
            identifiers = {}

        # Remove source identifier
        if self._service.source_key in identifiers:
            del identifiers[self._service.source_key]

        return identifiers

    def _get_parameter(self, key, show, season=None, episode=None):
        for obj in [episode, season, show]:
            if not obj:
                continue

            return obj.parameters.get(key)

        return None
