from trakt.interfaces.base import Interface


class SyncInterface(Interface):
    path = 'sync'

    def last_activities(self):
        return self.get_data(
            self.http.get('lastactivities')
        )

    def playback(self):
        return self.get_data(
            self.http.get('playback')
        )
