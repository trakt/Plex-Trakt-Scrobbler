from core.helpers import build_repr
from core.model import DictModel
from data.client import Client
from data.user import User

from plex_metadata import Matcher


class WatchSession(object):
    def __init__(self, key, metadata, session, guid, state):
        self.key = key

        # Plex
        self.metadata = metadata
        self.session = session
        self.guid = guid

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
    def from_session(session, metadata, guid, state):
        return WatchSession(
            session.key,
            metadata, session, guid,
            state
        )

    @staticmethod
    def from_info(info, metadata, client_section=None):
        if not info:
            return None

        # Build user object
        user = None

        if info['user_id'] and info['user_name']:
            user = User(info['user_id'], info['user_name'])

        # Build client object
        client = None

        if client_section is not None:
            client = Client.from_section(client_section)
        elif info.get('client'):
            client = Client(
                info['machineIdentifier'],
                info['client'],
                info['address']
            )

        return WatchSession(
            'logging-%s' % info.get('machineIdentifier'),
            info['ratingKey'],
            metadata, info['state'],

            user=user,
            client=client
        )

    def __repr__(self):
        return build_repr(self, [
            'key', 'item_key', 'cur_state',
            'user', 'client'
        ])

    def __str__(self):
        return self.__repr__()
