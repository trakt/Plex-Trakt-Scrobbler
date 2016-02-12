from plugin.managers.core.base import Get, Update
from plugin.scrobbler.core.session_prefix import SessionPrefix

from plex_metadata import Metadata, Guid
import logging

log = logging.getLogger(__name__)


class Base(object):
    @classmethod
    def build_session_key(cls, session_key):
        if type(session_key) is str:
            return session_key

        # Prepend session prefix
        session_prefix = SessionPrefix.get()

        return '%s:%s' % (
            session_prefix,
            session_key
        )


class GetSession(Get, Base):
    pass


class UpdateSession(Update, Base):
    @staticmethod
    def get_account(result):
        # Try retrieve account from client
        client = result.get('client')

        try:
            client_account_id = client.account_id if client else None
        except KeyError:
            client_account_id = None

        if client_account_id:
            # Valid account found
            return client_account_id

        # Try retrieve account from user
        user = result.get('user')

        try:
            user_account_id = user.account_id if user else None
        except KeyError:
            user_account_id = None

        if user_account_id:
            # Valid account found
            return user_account_id

        return None

    @staticmethod
    def get_metadata(rating_key):
        # Retrieve metadata for `rating_key`
        try:
            metadata = Metadata.get(rating_key)
        except NotImplementedError, e:
            log.debug('%r, ignoring session', e.message)
            return None, None

        # Ensure metadata was returned
        if not metadata:
            return None, None

        # Queue flush for metadata cache
        Metadata.cache.flush_queue()

        # Validate metadata
        if metadata.type not in ['movie', 'episode']:
            log.info('Ignoring metadata with type %r for rating_key %r', metadata.type, rating_key)
            return metadata, None

        # Parse guid
        guid = Guid.parse(metadata.guid)

        return metadata, guid

    @staticmethod
    def get_progress(duration, view_offset):
        if duration is None:
            return None

        return round((float(view_offset) / duration) * 100, 2)
