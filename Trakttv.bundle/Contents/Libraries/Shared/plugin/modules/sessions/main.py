from plugin.core.helpers.thread import synchronized
from plugin.modules.core.base import Module
from plugin.preferences import Preferences

from datetime import datetime, timedelta
from threading import RLock
import logging

CLEANUP_INTERVAL = timedelta(minutes=1)
SESSION_TIMEOUT = timedelta(minutes=2)

log = logging.getLogger(__name__)


class Sessions(Module):
    __key__ = 'sessions'

    def __init__(self):
        self._lock = RLock()

        self._by_account = {}
        self._by_session_key = {}

        self._cleaned_at = None
        self._idle_since = datetime.min

    def is_account_streaming(self, account, rating_key=None):
        if type(account) is not int:
            account = account.id

        # Cleanup stale sessions
        self.cleanup()

        # Try find matching `account` and `rating_key`
        return self._by_account.get(account, {}).get(rating_key, False)

    def is_idle(self):
        # Cleanup stale sessions
        self.cleanup()

        # Check if server has been idle for `sync.idle_delay` seconds
        return self._idle_since and datetime.utcnow() - self._idle_since > timedelta(minutes=Preferences.get('sync.idle_delay'))

    def is_streaming(self):
        # Cleanup stale sessions
        self.cleanup()

        # Check if there is any active sessions
        if self._by_session_key:
            return True

        return False

    #
    # Session methods
    #

    @synchronized(lambda self: self._lock)
    def cleanup(self, force=False):
        if not force and self._cleaned_at and datetime.utcnow() - self._cleaned_at < CLEANUP_INTERVAL:
            return 0

        states = self._by_session_key.values()
        removed = 0

        for state in states:
            if state.is_stale() and self.delete(state):
                removed += 1

        if removed:
            log.info('Removed %d stale session(s)', removed)
        else:
            log.debug('Removed %d stale session(s)', removed)

        self._cleaned_at = datetime.utcnow()
        return removed

    @synchronized(lambda self: self._lock)
    def create(self, session):
        if session.state not in ['create', 'start', 'pause']:
            return

        # Retrieve session parameters
        account_id = self._get_session_account_id(session)
        rating_key = session.rating_key

        # Build session key
        session_key = self._get_session_key(session)

        if session_key is None or session_key.endswith(':None'):
            return

        # Construct session
        state = SessionState(session_key, account_id, rating_key)

        # Ensure account exists in `active`
        if account_id not in self._by_account:
            self._by_account[account_id] = {}

        # Store item in `active`
        self._by_account[account_id][rating_key] = state

        # Store session in `active_by_id` map
        self._by_session_key[session_key] = state

        # Clear idle status
        self._idle_since = None

    @synchronized(lambda self: self._lock)
    def delete(self, state):
        # Remove item from `active` dictionary
        if state.account_id in self._by_account and state.rating_key in self._by_account[state.account_id]:
            try:
                del self._by_account[state.account_id][state.rating_key]
            except KeyError:
                pass
        else:
            log.debug('Unable to find item %r for account %r', state.rating_key, state.account_id)

        # Remove item from `active_by_id` dictionary
        if state.session_key in self._by_session_key:
            try:
                del self._by_session_key[state.session_key]
            except KeyError:
                pass
        else:
            log.debug('Unable to find session %r', state.session_key)

        # Update idle status
        if not self._by_session_key:
            self._idle_since = datetime.utcnow()

        return True

    @synchronized(lambda self: self._lock)
    def replace(self, state, session):
        # Remove current state
        self.delete(state)

        # Create new session
        self.create(session)

    @synchronized(lambda self: self._lock)
    def update(self, session):
        # Retrieve session parameters
        s_account_id = self._get_session_account_id(session)

        if s_account_id is None:
            return

        # Build session key
        session_key = self._get_session_key(session)

        if session_key is None:
            return

        # Check if session exists
        if session_key not in self._by_session_key:
            self.create(session)
            return

        # Check if an update is required
        state = self._by_session_key[session_key]

        if state.account_id != s_account_id or state.rating_key != session.rating_key:
            # Replace session details
            self.replace(state, session)
        elif session.state == 'stop':
            # Delete current session
            self.delete(state)
        else:
            # Update session
            state.update(session)

    #
    # Event handlers
    #

    @synchronized(lambda self: self._lock)
    def on_created(self, session):
        # Store session
        self.create(session)

        # Display active session message
        self._log()

    @synchronized(lambda self: self._lock)
    def on_updated(self, session):
        # Update session
        self.update(session)

        # Display active session message
        self._log()

    #
    # Helpers
    #

    def _log(self):
        if not self._by_session_key:
            return

        log.debug('%d active session(s): %r', len(self._by_session_key), self._by_session_key)

    @classmethod
    def _get_session_account_id(cls, session):
        try:
            return session.account_id
        except KeyError:
            return None

    @classmethod
    def _get_session_key(cls, session):
        if session.session_key is None:
            return None

        try:
            return int(session.session_key)
        except ValueError:
            pass

        return session.session_key


class SessionState(object):
    def __init__(self, session_key, account_id, rating_key):
        self.session_key = session_key

        self.account_id = account_id
        self.rating_key = rating_key

        self.seen_at = datetime.utcnow()

    def is_stale(self):
        return datetime.utcnow() - self.seen_at > SESSION_TIMEOUT

    def update(self, session):
        self.seen_at = datetime.utcnow()

    def __repr__(self):
        return '<Session %s>' % (
            ', '.join([
                ('%s: %r' % (key, getattr(self, key))) for key in [
                    'session_key',

                    'account_id',
                    'rating_key',

                    'seen_at'
                ]
            ])
        )
