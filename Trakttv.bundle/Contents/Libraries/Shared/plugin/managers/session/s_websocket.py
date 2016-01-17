from plugin.core.helpers.variable import to_integer, merge, resolve
from plugin.core.session_status import SessionStatus
from plugin.managers.core.base import Manager
from plugin.managers.client import ClientManager
from plugin.managers.core.exceptions import FilteredException
from plugin.managers.session.base import GetSession, UpdateSession
from plugin.managers.user import UserManager
from plugin.models import Session

from datetime import datetime
from plex import Plex
import apsw
import logging
import peewee


log = logging.getLogger(__name__)


class GetWSession(GetSession):
    def __call__(self, info):
        session_key = to_integer(info.get('sessionKey'))

        return super(GetWSession, self).__call__(
            Session.session_key == self.build_session_key(session_key)
        )

    def or_create(self, info, fetch=False):
        session_key = to_integer(info.get('sessionKey'))

        try:
            # Create new session
            obj = self.manager.create(
                rating_key=to_integer(info.get('ratingKey')),
                session_key=self.build_session_key(session_key),

                state='create'
            )

            # Update newly created object
            self.manager.update(obj, info, fetch)

            # Update active sessions
            SessionStatus.on_created(obj)

            return obj
        except (apsw.ConstraintError, peewee.IntegrityError):
            # Return existing object
            return self(info)


class UpdateWSession(UpdateSession):
    def __call__(self, obj, info, fetch=False):
        data = self.to_dict(obj, info, fetch)

        success = super(UpdateWSession, self).__call__(
            obj, data
        )

        SessionStatus.on_updated(obj)
        return success

    def to_dict(self, obj, info, fetch=False):
        fetch = resolve(fetch, obj, info)

        view_offset = to_integer(info.get('viewOffset'))

        result = {
            'rating_key': to_integer(info.get('ratingKey')),
            'view_offset': view_offset,

            'updated_at': datetime.utcnow()
        }

        if not fetch:
            # Return simple update
            return merge(result, {
                'progress': self.get_progress(obj.duration, view_offset)
            })

        # Retrieve session key
        session_key = to_integer(info.get('sessionKey'))

        if not session_key:
            log.warn('Missing session key, unable to fetch session details')
            return result

        # Retrieve session details
        log.debug('Fetching details for session #%s', session_key)

        p_item = Plex['status'].sessions().get(session_key)

        if not p_item:
            log.warn('Unable to find session with key %r', session_key)
            return result

        # Retrieve metadata and guid
        p_metadata, guid = self.get_metadata(p_item.rating_key)

        if not p_metadata:
            log.warn('Unable to retrieve metadata for rating_key %r', p_item.rating_key)
            return result

        if not guid:
            return merge(result, {
                'duration': p_metadata.duration,
                'progress': self.get_progress(p_metadata.duration, view_offset)
            })

        try:
            # Create/Retrieve `Client` for session
            result['client'] = ClientManager.get.or_create(
                p_item.session.player,

                fetch=True,
                match=True,
                filtered_exception=True
            )

            # Create/Retrieve `User` for session
            result['user'] = UserManager.get.or_create(
                p_item.session.user,

                fetch=True,
                match=True,
                filtered_exception=True
            )

            # Pick account from `client` or `user` objects
            result['account'] = self.get_account(result)
        except FilteredException:
            log.debug('Activity has been filtered')

            result['client'] = None
            result['user'] = None

            result['account'] = None

        return merge(result, {
            'duration': p_metadata.duration,
            'progress': self.get_progress(p_metadata.duration, view_offset)
        })


class WSessionManager(Manager):
    get = GetWSession
    update = UpdateWSession

    model = Session
