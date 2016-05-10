from oem.media.show.identifier import EpisodeIdentifier
from oem.media.show.match import EpisodeMatch

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
        elif not season:
            log.warn('Unable to find season %r in show %r', identifier.season_num, show)
            return best

        # Episode
        result = self._match_episode(show, season, identifier)

        if result:
            best = result

        # Return best result
        return best

    def _match_show(self, show, identifier):
        if 'default_season' not in show.parameters:
            return None

        # Default Season
        try:
            default_season = int(show.parameters['default_season'])
        except Exception:
            return None

        # Build episode match
        return EpisodeMatch(
            self._get_identifiers(show),
            season_num=default_season,
            episode_num=identifier.episode_num + int(show.parameters.get('episode_offset', 0))
        )

    def _match_season(self, show, identifier):
        # Try retrieve matching season
        season = show.seasons.get(str(identifier.season_num)) or show.seasons.get('a')

        if not season:
            return None, None

        if season.number == 'a':
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

        # Default Season
        default_season = 1

        if 'default_season' in season.parameters:
            try:
                default_season = int(season.parameters['default_season'])
            except Exception:
                pass

        return season, EpisodeMatch(
            self._get_identifiers(show, season),
            season_num=default_season,
            episode_num=identifier.episode_num
        )

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
            return EpisodeMatch(
                self._get_identifiers(show, season, episode),
                season_num=season_num,
                episode_num=episode_num
            )

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
