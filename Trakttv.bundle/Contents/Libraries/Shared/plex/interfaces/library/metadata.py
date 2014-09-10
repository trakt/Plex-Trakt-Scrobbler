from plex.interfaces.core.base import Interface


class LibraryMetadataInterface(Interface):
    path = 'library/metadata'

    def all_leaves(self, key):
        response = self.http.get(key, 'allLeaves')

        return self.parse(response, {
            'MediaContainer': ('EpisodeContainer', {
                'Video': {
                    'episode': 'Episode'
                }
            })
        })

    def children(self, key):
        response = self.http.get(key, 'children')

        return self.parse(response, {
            'MediaContainer': ('SeasonContainer', {
                'Directory': {
                    'season': 'Season'
                }
            })
        })
