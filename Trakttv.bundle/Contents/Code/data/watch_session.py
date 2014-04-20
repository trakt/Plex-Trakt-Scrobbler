from core.model import DictModel
from data.client import Client
from data.user import User


class WatchSession(DictModel):
    root_key = 'nowPlaying'

    def __init__(self, session_key=None, item_key=None, metadata=None, state=None, user=None, client=None):
        """
        :type metadata: ?
        :type state: str
        :type user: User
        """

        super(WatchSession, self).__init__(session_key)

        self.item_key = item_key

        # Plex
        self.metadata = metadata
        self.user = user
        self.client = client

        # States
        self.skip = False
        self.scrobbled = False
        self.watching = False

        # Multi-episode scrobbling
        self.cur_episode = None

        self.progress = None
        self.cur_state = state

        self.paused_since = None
        self.last_view_offset = 0

        self.update_required = False
        self.last_updated = Datetime.FromTimestamp(0)

    def get_type(self):
        """
        :rtype: str or None
        """

        if not self.metadata or not self.metadata.get('type'):
            return None

        media_type = self.metadata.get('type')

        if media_type == 'episode':
            return 'show'

        return media_type

    def get_title(self):
        if not self.metadata:
            return None

        if 'grandparent_title' in self.metadata:
            return self.metadata['grandparent_title']

        return self.metadata.get('title')

    def reset(self):
        self.scrobbled = False
        self.watching = False

        self.last_updated = Datetime.FromTimestamp(0)

    @classmethod
    def object_from_json(cls, key, value):
        if key == 'user':
            return User.from_json(value)

        if key == 'client':
            return Client.from_json(value)

        return value

    @staticmethod
    def from_section(section, state, metadata, client_section=None):
        """
        :type section: ?
        :type state: str

        :rtype: WatchSession or None
        """

        if not section:
            return None

        return WatchSession(
            section.get('sessionKey'),
            section.get('ratingKey'),
            metadata, state,
            user=User.from_section(section),
            client=Client.from_section(client_section)
        )

    @staticmethod
    def from_info(info, metadata, client_section):
        if not info:
            return None

        return WatchSession(
            'logging-%s' % info.get('machineIdentifier'),
            info['ratingKey'],
            metadata,
            info['state'],
            client=Client.from_section(client_section)
        )
