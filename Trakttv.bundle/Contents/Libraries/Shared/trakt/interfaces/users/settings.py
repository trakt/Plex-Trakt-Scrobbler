from trakt.interfaces.base import Interface


class UsersSettingsInterface(Interface):
    path = 'users/settings'

    def get(self):
        response = self.http.get()

        return self.get_data(response)
