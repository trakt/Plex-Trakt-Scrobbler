from trakt.interfaces.base import Interface, authenticated


class MediaInterface(Interface):
    @authenticated
    def cancel_watching(self, credentials=None):
        """Notify trakt that a user has stopped watching a show."""
        response = self.request(
            'cancelwatching',
            credentials=credentials
        )

        return self.get_data(response, catch_errors=False)

    @authenticated
    def send(self, action, data, credentials=None):
        response = self.request(
            action,
            data=data,
            credentials=credentials
        )

        return self.get_data(response, catch_errors=False)
