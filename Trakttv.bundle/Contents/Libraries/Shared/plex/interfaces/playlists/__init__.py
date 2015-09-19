from plex.core.idict import idict
from plex.interfaces.core.base import Interface


class PlaylistsInterface(Interface):
    path = 'playlists'

    def all(self, type=15, sort=None, playlist_type=None, smart=None):
        response = self.http.get('all', query=[
            ('type', type),
            ('sort', sort),
            ('playlistType', playlist_type),
            ('smart', smart)
        ])

        return self.parse(response, idict({
            'MediaContainer': ('MediaContainer', idict({
                'Playlist': 'Playlist'
            }))
        }))

    def create(self, type, title, uri, smart=False):
        response = self.http.post(query=[
            ('type', type),
            ('title', title),
            ('uri', uri),

            ('smart', int(smart))
        ])

        return self.parse(response, idict({
            'MediaContainer': ('MediaContainer', idict({
                'Playlist': 'Playlist'
            }))
        }))

    def delete(self, key):
        response = self.http.delete(key)

        return response.status_code == 200

    def get(self, key):
        response = self.http.get(key)

        return self.parse(response, idict({
            'MediaContainer': ('MediaContainer', idict({
                'Playlist': 'Playlist'
            }))
        }))
