from plugin.managers import AccountManager
from plugin.managers.core.base import Manager
from plugin.managers.client import ClientManager
from plugin.managers.user import UserManager
from plugin.core.helpers.variable import to_integer
from plugin.models import db, Session, Account

from plex import Plex
from plex_metadata import Metadata, Guid
import logging


log = logging.getLogger(__name__)


class SessionManager(Manager):
    @classmethod
    def from_logging(cls, info):
        raise NotImplementedError()

    @classmethod
    def from_websocket(cls, info):
        return WebSocket.from_websocket(info)


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
    def from_websocket(cls, info):
        session_key = to_integer(info.get('sessionKey'))

        return cls.get_or_create(
            info,

            Session.session_key == session_key,

            on_create={
                'session_key': session_key
            }
        )

    @classmethod
    def to_dict(cls, info, fetch=False):
        result = {
            'rating_key': to_integer(info.get('ratingKey')),

            'state': info.get('state'),
            'view_offset': to_integer(info.get('viewOffset'))
        }

        if not fetch:
            # Return simple update
            return result

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

        # Pick account from `client` or `user` objects
        result['account'] = cls.get_account(result['client'], result['user'])

        return result
