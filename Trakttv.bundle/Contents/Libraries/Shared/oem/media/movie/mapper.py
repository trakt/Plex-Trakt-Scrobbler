from __future__ import absolute_import, division, print_function

from oem.media.movie.identifier import MovieIdentifier
from oem.media.movie.match import MovieMatch
from oem.media.show import EpisodeIdentifier

from copy import deepcopy


class MovieMapper(object):
    def __init__(self, service):
        self._service = service

    def match(self, movie, identifier, resolve_mappings=True):
        if identifier is not None and not identifier.valid:
            raise ValueError('Invalid value provided for "identifier" parameter')

        if isinstance(identifier, EpisodeIdentifier) and identifier.season_num != 1:
            return None

        # Movie
        best = self._match_movie(movie, identifier)

        # Part
        result = self._match_part(movie, identifier)

        if result:
            best = result

        # Return best result
        return best

    def _match_movie(self, movie, identifier):
        if isinstance(identifier, MovieIdentifier) and identifier.part is not None and identifier.part > 1:
            return None

        if isinstance(identifier, EpisodeIdentifier) and identifier.episode_num != 1:
            return None

        # Retrieve progress
        progress = None

        if identifier:
            progress = identifier.progress

        # Create movie match
        return MovieMatch(
            self._get_identifiers(movie),
            progress=progress
        )

    def _match_part(self, movie, identifier):
        if isinstance(identifier, MovieIdentifier):
            part_num = identifier.part
        elif isinstance(identifier, EpisodeIdentifier):
            part_num = identifier.episode_num
        else:
            part_num = 1

        # Retrieve part
        part = movie.parts.get(str(part_num))

        if not part:
            return None

        # Retrieve progress
        progress = None

        if identifier:
            progress = identifier.progress

        # Create movie match
        return MovieMatch(
            self._get_identifiers(part),
            progress=progress
        )

    def _get_identifiers(self, movie):
        # Retrieve identifiers from objects
        identifiers = movie.identifiers

        # Copy identifiers
        if identifiers:
            identifiers = deepcopy(identifiers)
        else:
            identifiers = {}

        # Remove source identifier
        if self._service.source_key in identifiers:
            del identifiers[self._service.source_key]

        return identifiers
