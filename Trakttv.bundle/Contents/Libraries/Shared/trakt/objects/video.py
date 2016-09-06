from trakt.core.helpers import from_iso8601
from trakt.objects.core.helpers import update_attributes
from trakt.objects.media import Media


class Video(Media):
    def __init__(self, client, keys=None, index=None):
        super(Video, self).__init__(client, keys, index)

        self.last_watched_at = None
        """
        :type: :class:`~python:datetime.datetime`

        Timestamp of when this item was last watched (or `None`)
        """

        self.collected_at = None
        """
        :type: :class:`~python:datetime.datetime`

        Timestamp of when this item was added to your collection (or `None`)
        """

        self.paused_at = None
        """
        :type: :class:`~python:datetime.datetime`

        Timestamp of when this item was paused (or `None`)
        """

        self.plays = None
        """
        :type: :class:`~python:int`

        Number of plays (or `None`)
        """

        self.progress = None
        """
        :type: :class:`~python:float`

        Playback progress for item (or `None`)
        """

        # Flags
        self.is_watched = None
        """
        :type: :class:`~python:bool`

        Flag indicating this item has been watched (or `None`)
        """

        self.is_collected = None
        """
        :type: :class:`~python:bool`

        Flag indicating this item has been collected (or `None`)
        """

    def _update(self, info=None, is_watched=None, is_collected=None, **kwargs):
        super(Video, self)._update(info, **kwargs)

        update_attributes(self, info, [
            'plays',
            'progress'
        ])

        # Set timestamps
        if 'last_watched_at' in info:
            self.last_watched_at = from_iso8601(info.get('last_watched_at'))

        if 'collected_at' in info:
            self.collected_at = from_iso8601(info.get('collected_at'))

        if 'paused_at' in info:
            self.paused_at = from_iso8601(info.get('paused_at'))

        # Set flags
        if is_watched is not None:
            self.is_watched = is_watched

        if is_collected is not None:
            self.is_collected = is_collected
