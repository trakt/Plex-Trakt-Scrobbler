from plex.interfaces.core.base import Interface


class LibraryMetadataInterface(Interface):
    path = 'library/metadata'

    def all_leaves(self, key):
        response = self.http.get(key, 'allLeaves')

        return self.parse(response, {
            'MediaContainer': {
                '_': 'viewGroup',

                'episode': ('ShowLeavesContainer', {
                    'Video': {
                        'episode': 'Episode'
                    }
                }),

                'track': ('ArtistLeavesContainer', {
                    'Track': 'Track'
                })
            }
        })

    def children(self, key):
        response = self.http.get(key, 'children')

        return self.parse(response, {
            'MediaContainer': {
                '_': 'viewGroup',

                # ---------------------------------------
                # Music
                # ---------------------------------------
                'album': ('ArtistChildrenContainer', {
                    'Directory': {
                        'album': 'Album'
                    }
                }),

                'track': ('AlbumChildrenContainer', {
                    'Track': 'Track'
                }),

                # ---------------------------------------
                # TV
                # ---------------------------------------
                'season': ('ShowChildrenContainer', {
                    'Directory': {
                        'season': 'Season'
                    }
                }),

                'episode': ('SeasonChildrenContainer', {
                    'Video': {
                        'episode': 'Episode'
                    }
                })
            }
        })
