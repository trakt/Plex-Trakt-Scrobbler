from core.helpers import build_repr, spawn
from core.logger import Logger
from data.model import Model

from jsonpickle.unpickler import ClassRegistry
from plex_metadata import Matcher
from Queue import PriorityQueue
from threading import Thread
from trakt import Trakt

log = Logger('pts.scrobbler')


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
        self.active = False

        self.skip = False
        self.filtered = False
        self.deleted = False

        # Requests/Actions
        self.action_queue = PriorityQueue()
        self.action_thread = None

        self.actions_sent = []
        self.actions_performed = []

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
        self.active = False

        self.last_updated = Datetime.FromTimestamp(0)

    def queue(self, action, request, priority=3):
        if priority == 0:
            log.info('Maximum retries exceeded for "%s" action', action)
            return False

        # Store in queue
        self.action_queue.put((priority, action, request))

        log.debug('Queued "%s" action (priority: %s)', action, priority)

        # Ensure action thread has started
        if not self.action_thread:
            self.action_thread = spawn(self.process_actions)

        return True

    def process_actions(self):
        log.debug('process_actions() thread - started')

        while not self.deleted:
            priority, action, request = self.action_queue.get()

            log.debug('Processing "%s" action (priority: %s)', action, priority)

            # Ensure we don't send duplicate actions
            if self.actions_sent and self.actions_sent[-1] == action:
                log.info('Ignoring duplicate "%s" action', action)
                continue

            # Only send a "start" action if we haven't scrobbled yet
            if action == 'start' and 'scrobble' in self.actions_performed:
                log.info('Ignoring "%s" action, session already scrobbled', action)
                continue

            # Send action to trakt.tv
            response = Trakt['scrobble'].action(action, **request)

            performed = response.get('action') if response else None

            if not performed:
                log.warn('Unable to send "%s" action', action)

                # Retry request
                self.queue(action, request, priority - 1)

                continue

            log.debug('Performed "%s" action on trakt.tv', performed)

            # Update action history
            self.actions_sent.append(action)
            self.actions_performed.append(performed)

        log.debug('process_actions() thread - finished')

    def delete(self):
        super(WatchSession, self).delete()

        # Set `deleted` flag
        self.deleted = True

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
            'key', 'cur_state', 'progress',
            'user', 'client'
        ])

    def __str__(self):
        return self.__repr__()


ClassRegistry.register('watch_session.WatchSession', WatchSession)
