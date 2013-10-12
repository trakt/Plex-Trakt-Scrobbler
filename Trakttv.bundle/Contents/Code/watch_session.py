from dict_object import DictObject
from user import User
from pms import PMS


class WatchSession(DictObject):
    root_key = 'nowPlaying'

    def __init__(self, session_key=None, metadata=None, state=None, user=None):
        """
        :type metadata: ?
        :type state: str
        :type user: User
        """

        super(WatchSession, self).__init__(session_key)

        self.metadata = metadata
        self.user = user

        self.skip = False
        self.scrobbled = False

        self.progress = None
        self.cur_state = state
        self.paused_since = None

        self.last_view_offset = 0
        self.last_updated = Datetime.FromTimestamp(0)

    def get_type(self):
        """
        :rtype: str or None
        """

        if not self.metadata.get('type'):
            return None
        media_type = self.metadata.get('type')

        if media_type == 'episode':
            if self.metadata.get('tvdb_id'):
                return 'show'

        if media_type == 'movie':
            if self.metadata.get('imdb_id') or self.metadata.get('tmdb_id'):
                return 'movie'

        return None

    def get_title(self):
        if not self.metadata:
            return None

        return self.metadata.get('title')

    @classmethod
    def object_from_json(cls, key, value):
        if key == 'user':
            return User.from_json(value)

        return value

    @staticmethod
    def from_section(section, state):
        """
        :type section: ?
        :type state: str

        :rtype: WatchSession or None
        """

        if not section:
            return None

        return WatchSession(
            section.get('sessionKey'),
            PMS.metadata(section.get('ratingKey')),
            state, User.from_section(section)
        )
