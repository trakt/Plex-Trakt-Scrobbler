from plex.core.idict import idict
from plex.interfaces.core.base import Interface


class PlaylistItemsInterface(Interface):
    path = 'playlists/*/items'

    def all(self, playlist_id, include_related=None, start=None, size=None):
        response = self.http.get('/playlists/%s/items' % playlist_id, query=[
            ('includeRelated', include_related),

            ('X-Plex-Container-Start', start),
            ('X-Plex-Container-Size', size),
        ])

        return self.parse(response, idict({
            'MediaContainer': ('PlaylistItemContainer', idict({
                'Directory': {
                    'album':    'Album',
                    'artist':   'Artist',

                    'season':   'Season',
                    'show':     'Show'
                },
                'Video': {
                    'episode':  'Episode',
                    'clip':     'Clip',
                    'movie':    'Movie'
                },

                'Track': 'Track'
            }))
        }))

    def add(self, playlist_id, item_uri):
        response = self.http.put('/playlists/%s/items' % playlist_id, query=[
            ('uri', item_uri)
        ])

        return self.parse(response, idict({
            'MediaContainer': ('MediaContainer', idict({
                'Playlist': 'Playlist'
            }))
        }))

    def remove(self, playlist_id, item_id):
        response = self.http.delete('/playlists/%s/items/%s' % (playlist_id, item_id))

        return self.parse(response, idict({
            'MediaContainer': ('MediaContainer', idict({
                'Playlist': 'Playlist'
            }))
        }))

    def move(self, playlist_id, item_id, after=None):
        response = self.http.put('/playlists/%s/items/%s/move' % (playlist_id, item_id), query=[
            ('after', after)
        ])

        return self.parse(response, idict({
            'MediaContainer': ('MediaContainer', idict({
                'Playlist': 'Playlist'
            }))
        }))
