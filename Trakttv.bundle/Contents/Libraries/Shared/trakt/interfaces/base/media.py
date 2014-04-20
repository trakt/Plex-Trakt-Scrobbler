from trakt.interfaces.base import Interface, authenticated


class MediaInterface(Interface):
    @authenticated
    def cancel_watching(self, credentials=None):
        """Notify trakt that a user has stopped watching a show."""
        return self.action(
            'cancelwatching',
            credentials=credentials
        )
