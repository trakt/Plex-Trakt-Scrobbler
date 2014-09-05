from plex.interfaces.core.base import Interface


class LibraryInterface(Interface):
    path = 'library'

    def metadata(self, rating_key):
        response = self.http.get('metadata', rating_key)

        return self.parse(response, {
            'MediaContainer': ('MediaContainer', {
                'Directory': {
                    'album':    'Album',
                    'season':   'Season',
                    'show':     'Show'
                },
                'Video': {
                    'episode':  'Episode',
                    'movie':    'Movie'
                }
            })
        })

    def on_deck(self):
        raise NotImplementedError()

    def recently_added(self):
        response = self.http.get('recentlyAdded')

        return self.parse(response, {
            'MediaContainer': ('MediaContainer', {
                'Directory': {
                    'album':    'Album',
                    'season':   'Season'
                },
                'Video': {
                    'movie':    'Movie'
                }
            })
        })

    def sections(self):
        response = self.http.get('sections')

        return self.parse(response, {
            'MediaContainer': ('SectionContainer', {
                'Directory': ('Section', {
                    'Location': 'Location'
                })
            })
        })
