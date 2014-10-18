from plex.interfaces.core.base import Interface


class StatusInterface(Interface):
    path = 'status'

    def sessions(self):
        response = self.http.get('sessions')

        return self.parse(response, {
            'MediaContainer': ('SessionContainer', {
                'Track': 'Track',

                'Video': {
                    'episode':  'Episode',
                    'movie':    'Movie'
                }
            })
        })
