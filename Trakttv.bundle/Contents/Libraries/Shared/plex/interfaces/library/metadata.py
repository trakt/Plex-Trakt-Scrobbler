from plex.core.idict import idict
from plex.interfaces.core.base import Interface


class LibraryMetadataInterface(Interface):
    path = 'library/metadata'

    def all_leaves(self, key):
        response = self.http.get(key, 'allLeaves')

        return self.parse(response, idict({
            'MediaContainer': {
                '_': 'viewGroup',

                'episode': ('ShowLeavesContainer', idict({
                    'Video': {
                        'episode': 'Episode'
                    }
                })),

                'track': ('ArtistLeavesContainer', idict({
                    'Track': 'Track'
                }))
            }
        }))

    def children(self, key):
        response = self.http.get(key, 'children')

        return self.parse(response, idict({
            'MediaContainer': {
                '_': 'viewGroup',

                # ---------------------------------------
                # Music
                # ---------------------------------------
                'album': ('ArtistChildrenContainer', idict({
                    'Directory': {
                        'album': 'Album'
                    }
                })),

                'track': ('AlbumChildrenContainer', idict({
                    'Track': 'Track'
                })),

                # ---------------------------------------
                # TV
                # ---------------------------------------
                'season': ('ShowChildrenContainer', idict({
                    'Directory': {
                        'season': 'Season'
                    }
                })),

                'episode': ('SeasonChildrenContainer', idict({
                    'Video': {
                        'episode': 'Episode'
                    }
                }))
            }
        }))

    def update(self, key, **kwargs):
        response = self.http.put(key, query=kwargs.items())

        return response.status_code == 200
