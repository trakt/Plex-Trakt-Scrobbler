from plugin.core.helpers.variable import to_integer, merge
from plugin.managers.core.base import Manager
from plugin.managers.client import ClientManager
from plugin.managers.user import UserManager
from plugin.models import Session

from plex import Plex
from plex_metadata import Metadata, Guid
import logging


log = logging.getLogger(__name__)


class SessionManager(Manager):
    @classmethod
    def from_logging(cls, info):
        raise NotImplementedError()

    @classmethod
    def from_websocket(cls, info, fetch=False, update=True):
        return WebSocket.from_websocket(
            info,
            fetch=fetch,
            update=update
        )


class Base(Manager):
    model = Session

    account = None

    @classmethod
    def get_account(cls, client, user):
        if client and client.account_id:
            return client.account_id

        if user and user.account_id:
            return user.account_id

        return None

    @classmethod
    def get_metadata(cls, rating_key):
        # Retrieve metadata for `rating_key`
        try:
            metadata = Metadata.get(rating_key)
        except NotImplementedError, e:
            log.debug('%r, ignoring session', e.message)
            return None, None

        # Parse guid
        guid = Guid.parse(metadata.guid)

        return metadata, guid


class Logging(Base):
    @classmethod
    def create(cls, session, info):
        pass


class WebSocket(Base):
    @classmethod
    def from_websocket(cls, info, fetch=False, update=True):
        session_key = to_integer(info.get('sessionKey'))

        return cls.get_or_create(
            info,

            Session.session_key == session_key,

            fetch=fetch,
            update=update,

            on_create={
                'rating_key': to_integer(info.get('ratingKey')),
                'session_key': session_key,

                'state': 'create'
            }
        )

    @classmethod
    def to_dict(cls, obj, info, fetch=False):
        view_offset = to_integer(info.get('viewOffset'))

        result = {
            'view_offset': view_offset
        }

        if not fetch:
            # Return simple update
            return merge(result, {
                'progress': cls.get_progress(obj.duration, view_offset)
            })

        # Retrieve session
        session_key = to_integer(info.get('sessionKey'))

        p_item = Plex['status'].sessions().get(session_key)

        if not p_item:
            log.warn('Unable to find session with key %r', session_key)
            return result

        # Retrieve metadata and guid
        p_metadata, p_guid = cls.get_metadata(p_item.rating_key)

        if not p_metadata or not p_guid:
            log.warn('Unable to retrieve guid/metadata for session %r', session_key)
            return result

        # Store client + user in `result`
        result['client'] = ClientManager.from_session(p_item.session, fetch=True)
        result['user'] = UserManager.from_session(p_item.session, fetch=True)

        return merge(result, {
            # Pick account from `client` or `user` objects
            'account': cls.get_account(result['client'], result['user']),

            'duration': p_metadata.duration,
            'progress': cls.get_progress(p_metadata.duration, view_offset)
        })

    @classmethod
    def get_progress(cls, duration, view_offset):
        if duration is None:
            return None

        return round((float(view_offset) / duration) * 100, 2)
