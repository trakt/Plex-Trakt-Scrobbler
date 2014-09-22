from trakt.interfaces.base import Interface


class SyncInterface(Interface):
    path = 'sync'

    def last_activities(self):
        return self.http.get('lastactivities')

    def playback(self):
        return self.http.get('playback')
