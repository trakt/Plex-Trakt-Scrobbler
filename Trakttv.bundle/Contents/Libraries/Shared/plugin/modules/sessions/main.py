from plugin.core.helpers.thread import synchronized
from plugin.modules.core.base import Module

from datetime import datetime, timedelta
from threading import RLock
import logging

log = logging.getLogger(__name__)


class Sessions(Module):
    __key__ = 'sessions'

    def __init__(self):
        self._lock = RLock()

        self._by_account = {}
        self._by_session_key = {}

        self._idle_since = datetime.min

    def is_account_streaming(self, account, rating_key=None):
        if type(account) is not int:
            account = account.id

        return self._by_account.get(account, {}).get(rating_key, False)

    def is_idle(self):
        return self._idle_since and datetime.utcnow() - self._idle_since > timedelta(minutes=30)

    def is_streaming(self):
        if self._by_session_key:
            return True

        return False

    #
    # Session methods
    #

    @synchronized(lambda self: self._lock)
    def create(self, session):
        log.debug('create(%r)', session)

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
        log.debug('delete(%r)', state)

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
        log.debug('replace(%r, %r)', state, session)

        # Remove current state
        self.delete(state)

        # Create new session
        self.create(session)

    @synchronized(lambda self: self._lock)
    def update(self, session):
        log.debug('update(%r)', session)

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
        log.debug('on_created(%r)', session)

        # Store session
        self.create(session)

        log.debug('by_account_rating_key: %r, by_session_key: %r', self._by_account, self._by_session_key)

    @synchronized(lambda self: self._lock)
    def on_updated(self, session):
        log.debug('on_updated(%r)', session)

        # Update session
        self.update(session)

        log.debug('by_account_rating_key: %r, by_session_key: %r', self._by_account, self._by_session_key)

    #
    # Helpers
    #

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
