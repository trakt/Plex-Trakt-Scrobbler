from plex.interfaces.core.base import Interface


class RootInterface(Interface):
    def detail(self):
        response = self.http.get()

        return self.parse(response, {
            'MediaContainer': ('Detail', {
                'Directory': 'Directory'
            })
        })

    def version(self):
        detail = self.detail()

        if not detail:
            return None

        return detail.version

    def clients(self):
        response = self.http.get('clients')

        return self.parse(response, {
            'MediaContainer': ('Container', {
                'Server': 'Client'
            })
        })

    def players(self):
        pass

    def servers(self):
        response = self.http.get('servers')

        return self.parse(response, {
            'MediaContainer': ('Container', {
                'Server': 'Server'
            })
        })
