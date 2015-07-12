from plugin.managers.core.base import Update

from plex_metadata import Metadata, Guid
import logging

log = logging.getLogger(__name__)


class UpdateSession(Update):
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
