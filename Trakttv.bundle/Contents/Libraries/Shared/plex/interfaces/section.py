from plex.core.idict import idict
from plex.interfaces.core.base import Interface


class SectionInterface(Interface):
    path = 'library/sections'

    def all(self, key):
        response = self.http.get(key, 'all')

        return self.parse(response, idict({
            'MediaContainer': ('MediaContainer', idict({
                'Directory': {
                    'artist':   'Artist',
                    'show':     'Show'
                },
                'Video': {
                    'movie':    'Movie'
                }
            }))
        }))
