from core.helpers import build_repr, spawn
from core.logger import Logger
from plugin.data.model import Model, Property

from jsonpickle.unpickler import ClassRegistry
from plex_metadata import Matcher
from Queue import PriorityQueue
from threading import Lock
import Queue


log = Logger('pts.scrobbler')


class WatchSession(Model):
    group = 'WatchSession'

    deleted = Property(False, pickle=False)

    # Requests/Actions
    action_manager = Property(None, pickle=False)
    action_queued = Property(lambda: Lock(), pickle=False)

    action_queue = Property(lambda: PriorityQueue(), pickle=False)
    action_thread = Property(None, pickle=False)

    actions_sent = Property(lambda: [])
    actions_performed = Property(lambda: [])

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
            self.action_queued.acquire()

            # Wait for an action
            try:
                priority, action, request = self.action_queue.get(timeout=30)
            except Queue.Empty:
                self.action_queued.release()
                continue

            log.debug('Processing "%s" action (priority: %s)', action, priority)

            # Ensure we don't send duplicate actions
            if self.actions_sent and self.actions_sent[-1] == action:
                log.info('Ignoring duplicate "%s" action', action)

                self.action_queued.release()
                continue

            # Only send a "start" action if we haven't scrobbled yet
            if action == 'start' and 'scrobble' in self.actions_performed:
                log.info('Ignoring "%s" action, session already scrobbled', action)

                self.action_queued.release()
                continue

            # Queue action with `ActionManager`
            self.action_manager.queue_scrobble(
                self.metadata.rating_key,
                action, request,

                callback=self.on_action_response
            )

            # Update action history
            self.actions_sent.append(action)

        log.debug('process_actions() thread - finished')

    def on_action_response(self, response, priority, item):
        # Get request details
        kwargs = item.get('kwargs', {})
        action = kwargs.get('action')

        # Check if response failed
        if not response:
            log.warn('Unable to send "%s" action', action)

            # Request failed, release the lock
            self.action_queued.release()
            return

        # Get response details
        performed = response.get('action')

        log.debug('Performed "%s" action on trakt.tv', performed)
        self.actions_performed.append(performed)

        # Action performed, release the lock (so another action can be sent)
        self.action_queued.release()

    def delete(self):
        super(WatchSession, self).delete()

        # Set `deleted` flag
        self.deleted = True

    @classmethod
    def configure(cls, action_manager):
        cls.action_manager = action_manager

    @classmethod
    def is_active(cls, rating_key, f_validate=None):
        if not rating_key:
            return False

        # Ensure `rating_key` is a string
        rating_key = str(rating_key)

        sessions = cls.all(lambda ws:
            ws.metadata and
            ws.metadata.rating_key == rating_key
        )

        for key, ws in sessions:
            if f_validate and not f_validate(ws):
                continue

            if ws.active:
                return True

        return False

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
