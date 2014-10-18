from core.helpers import build_repr
from data.model import Model

from jsonpickle.unpickler import ClassRegistry
from plex_metadata import Matcher


class WatchSession(Model):
    group = 'WatchSession'

    def __init__(self, key, metadata, guid, state, session=None):
        super(WatchSession, self).__init__(key)

        # Plex
        self.metadata = metadata
        self.guid = guid
        self.session = session

        self.client = None

        # States
        self.skip = False
        self.filtered = False
        self.scrobbled = False
        self.watching = False

        # Multi-episode scrobbling
        self.cur_episode = None

        self.progress = None
        self.cur_state = state

        self.paused_since = None
        self.last_view_offset = None

        self.update_required = False
        self.last_updated = Datetime.FromTimestamp(0)

        # Private
        self.identifier_ = None
        self.user_ = None

    @property
    def type(self):
        if not self.metadata or not self.metadata.type:
            return None

        media_type = self.metadata.type

        if media_type == 'episode':
            return 'show'

        return media_type

    @property
    def identifier(self):
        if self.metadata is None:
            return None

        if self.identifier_ is None:
            self.identifier_ = Matcher.process(self.metadata)

        return self.identifier_

    @property
    def title(self):
        if not self.metadata:
            return None

        if self.metadata.type in ['season', 'episode']:
            return self.metadata.show.title

        return self.metadata.title

    @property
    def user(self):
        if self.session:
            return self.session.user

        return self.user_

    @user.setter
    def user(self, value):
        self.user_ = value

    def reset(self):
        self.scrobbled = False
        self.watching = False

        self.last_updated = Datetime.FromTimestamp(0)

    @staticmethod
    def from_session(session, metadata, guid, state):
        return WatchSession(
            session.key,
            metadata, guid, state,

            session=session
        )

    @staticmethod
    def from_info(info, metadata, guid):
        if not info:
            return None

        return WatchSession(
            'logging-%s' % info.get('machineIdentifier'),
            metadata, guid,
            info['state']
        )

    def __repr__(self):
        return build_repr(self, [
            'key', 'item_key', 'cur_state',
            'user', 'client'
        ])

    def __str__(self):
        return self.__repr__()


ClassRegistry.register('watch_session.WatchSession', WatchSession)
