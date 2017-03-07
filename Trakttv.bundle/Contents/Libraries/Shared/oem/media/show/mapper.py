from __future__ import absolute_import, division, print_function

from oem.core.exceptions import AbsoluteNumberRequiredError
from oem.media.movie.identifier import MovieIdentifier
from oem.media.show.identifier import EpisodeIdentifier
from oem.media.show.match import EpisodeMatch
from oem_framework.core.helpers import try_convert

from copy import deepcopy
import logging

log = logging.getLogger(__name__)


class ShowMapper(object):
    def __init__(self, service):
        self._service = service

    def match(self, show, identifier, resolve_mappings=True):
        if identifier is None:
            # Create identifier for S01E01
            identifier = EpisodeIdentifier(1, 1)
        elif isinstance(identifier, MovieIdentifier):
            # Convert movie identifier to S01E01
            identifier = EpisodeIdentifier(1, 1, progress=identifier.progress)

        # Validate identifier
        if identifier and not identifier.valid:
            raise ValueError('Invalid value provided for "identifier" parameter')

        # Show
        best = self._match_show(show, identifier)

        # Season
        season, result = self._match_season(show, identifier)

        if result:
            best = result

        if season:
            # Episode
            result = self._match_episode(
                show, season, identifier,
                resolve_mappings=resolve_mappings
            )

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
                episode_num=episode_num,

                progress=identifier.progress
            )
        else:
            if identifier.absolute_num is None:
                raise AbsoluteNumberRequiredError('Unable to match %r, an absolute number is required' % identifier)

            match = EpisodeMatch(
                self._get_identifiers(show),
                absolute_num=identifier.absolute_num,

                progress=identifier.progress
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
                absolute_num=identifier.absolute_num,

                progress=identifier.progress
            )

        # Look for matching season mapping
        for season_mapping in season.mappings:
            if not (season_mapping.start <= identifier.episode_num <= season_mapping.end):
                continue

            return season, EpisodeMatch(
                self._get_identifiers(show, season),
                int(season_mapping.season),
                identifier.episode_num + season_mapping.offset,

                progress=identifier.progress
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
            episode_num=episode_num,

            progress=identifier.progress
        )

        if not match.valid:
            return season, None

        return season, match

    def _match_episode(self, show, season, identifier, resolve_mappings=True):
        episode = season.episodes.get(str(identifier.episode_num))

        if not episode:
            return None

        if not resolve_mappings:
            match = EpisodeMatch(
                self._get_identifiers(show, season, episode),
                mappings=episode.mappings
            )

            if not match.valid:
                return None

            return match

        if identifier.part is not None and identifier.part - 1 < len(episode.mappings):
            # Parse episode mapping
            valid, match = self._parse_episode_mapping(
                show, season, episode, episode.mappings[identifier.part - 1],
                part=identifier.part
            )

            if valid:
                return match

        for episode_mapping in episode.mappings:
            # Parse timeline attributes
            progress = identifier.progress

            if episode_mapping.timeline:
                if identifier.progress is None:
                    raise ValueError('Missing required parameter "progress"')

                if 'source' in episode_mapping.timeline:
                    timeline_source = episode_mapping.timeline['source']

                    if not (timeline_source.start <= identifier.progress <= timeline_source.end):
                        continue

                    # Calculate progress
                    progress = (
                        float(identifier.progress - timeline_source.start) *
                        (100 / (timeline_source.end - timeline_source.start))
                    )
                elif 'target' in episode_mapping.timeline:
                    timeline_target = episode_mapping.timeline['target']

                    # Calculate progress
                    progress = (
                        timeline_target.start + (
                            float(identifier.progress) /
                            (100 / (timeline_target.end - timeline_target.start))
                        )
                    )

            # Parse episode mapping
            valid, match = self._parse_episode_mapping(
                show, season, episode, episode_mapping,
                progress=progress
            )

            if valid:
                return match

        return None

    def _parse_episode_mapping(self, show, season, episode, episode_mapping, progress=None, part=None):
        # Parse mapping attributes
        try:
            season_num = int(episode_mapping.season)
        except (TypeError, ValueError):
            return False, None

        try:
            episode_num = int(episode_mapping.number)
        except (TypeError, ValueError):
            return False, None

        # Return episode match
        match = EpisodeMatch(
            self._get_identifiers(show, season, episode),
            season_num=season_num,
            episode_num=episode_num,

            progress=progress,
            part=part
        )

        if not match.valid:
            return True, None

        return True, match

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
