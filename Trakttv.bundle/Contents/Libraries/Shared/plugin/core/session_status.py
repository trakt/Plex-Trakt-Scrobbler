from threading import Lock
import logging

log = logging.getLogger(__name__)


class SessionStatus(object):
    _active = {}
    _active_by_id = {}

    _lock = Lock()

    @classmethod
    def is_watching(cls, account, rating_key):
        if type(account) is not int:
            account = account.id

        return cls._active.get(account, {}).get(rating_key, False)

    @classmethod
    def on_created(cls, session):
        with cls._lock:
            cls._create(session)

    @classmethod
    def on_updated(cls, session):
        with cls._lock:
            cls._update(session)

    @classmethod
    def _create(cls, session):
        # Store session
        cls._store(session)

        log.debug('active: %r, active_by_id: %r', cls._active, cls._active_by_id)

    @classmethod
    def _delete(cls, account_id, rating_key, session_key):
        # Remove item from `active` dictionary
        if account_id in cls._active and rating_key in cls._active[account_id]:
            try:
                del cls._active[account_id][rating_key]
            except KeyError:
                pass
        else:
            log.debug('Unable to find item %r for account %r', rating_key, account_id)

        # Remove item from `active_by_id` dictionary
        if session_key in cls._active_by_id:
            try:
                del cls._active_by_id[session_key]
            except KeyError:
                pass
        else:
            log.debug('Unable to find session %r', session_key)

        return True

    @classmethod
    def _get_session_key(cls, session):
        if session.session_key is None:
            return None

        try:
            return int(session.session_key)
        except ValueError:
            pass

        return session.session_key

    @classmethod
    def _replace(cls, account_id, rating_key, session_key, session):
        # Remove previous session
        cls._delete(account_id, rating_key, session_key)

        # Store session
        cls._store(session)

    @classmethod
    def _store(cls, session):
        if session.state not in ['create', 'start', 'pause']:
            return

        # Retrieve parameters
        account_id = session.account_id
        rating_key = session.rating_key

        session_key = cls._get_session_key(session)

        if session_key is None:
            return

        # Ensure account exists in `active`
        if account_id not in cls._active:
            cls._active[account_id] = {}

        # Store item in `active`
        cls._active[account_id][rating_key] = True

        # Store session in `active_by_id` map
        cls._active_by_id[session_key] = (account_id, rating_key)

    @classmethod
    def _update(cls, session):
        session_key = cls._get_session_key(session)

        if session_key is None:
            return

        # Check if session exists
        if session_key not in cls._active_by_id:
            cls._create(session)
            return

        # Check if an update is required
        account_id, rating_key = cls._active_by_id[session_key]

        if account_id != session.account_id or rating_key != session.rating_key:
            # Replace session details
            cls._replace(account_id,  rating_key, session_key, session)
        elif session.state == 'stop':
            # Delete current session
            cls._delete(account_id, rating_key, session_key)

        log.debug('active: %r, active_by_id: %r', cls._active, cls._active_by_id)
