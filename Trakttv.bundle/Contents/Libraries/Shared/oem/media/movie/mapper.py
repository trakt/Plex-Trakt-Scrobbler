from oem.media.movie.match import MovieMatch
from oem.media.show import EpisodeIdentifier

from copy import deepcopy


class MovieMapper(object):
    def __init__(self, service):
        self._service = service

    def match(self, movie, identifier, resolve_mappings=True):
        if identifier is not None and not identifier.valid:
            raise ValueError('Invalid value provided for "identifier" parameter')

        if isinstance(identifier, EpisodeIdentifier) and (identifier.season_num != 1 or identifier.episode_num != 1):
            return None

        return self._match_movie(movie, identifier)

    def _match_movie(self, movie, identifier):
        return MovieMatch(self._get_identifiers(movie))

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
