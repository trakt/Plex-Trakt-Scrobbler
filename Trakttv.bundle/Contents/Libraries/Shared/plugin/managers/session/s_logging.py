from plugin.core.helpers.variable import to_integer, merge
from plugin.managers.core.base import Manager
from plugin.managers.client import ClientManager
from plugin.managers.core.exceptions import FilteredException
from plugin.managers.session.base import GetSession, UpdateSession
from plugin.managers.user import UserManager
from plugin.models import Session
from plugin.modules.core.manager import ModuleManager

from datetime import datetime
from exception_wrappers.libraries import apsw
import logging
import peewee

log = logging.getLogger(__name__)


class GetLSession(GetSession):
    def __call__(self, info):
        machine_identifier = info.get('machineIdentifier')

        if not machine_identifier:
            return None

        return super(GetLSession, self).__call__(
            Session.session_key == machine_identifier
        )

    def or_create(self, info, fetch=False):
        machine_identifier = info.get('machineIdentifier')

        if not machine_identifier:
            log.info('No machine identifier available, unable to create session')
            return None

        try:
            # Create new session
            obj = self.manager.create(
                rating_key=to_integer(info.get('ratingKey')),
                session_key=machine_identifier,

                state='create'
            )

            # Update newly created object
            self.manager.update(obj, info, fetch)

            # Update active sessions
            ModuleManager['sessions'].on_created(obj)

            return obj
        except (apsw.ConstraintError, peewee.IntegrityError):
            # Return existing object
            return self(info)


class UpdateLSession(UpdateSession):
    def __call__(self, obj, info, fetch=False):
        data = self.to_dict(obj, info, fetch)

        success = super(UpdateLSession, self).__call__(
            obj, data
        )

        ModuleManager['sessions'].on_updated(obj)
        return success

    def to_dict(self, obj, info, fetch=False):
        view_offset = to_integer(info.get('time'))
        rating_key = info.get('ratingKey')

        result = {
            'view_offset': view_offset,

            'updated_at': datetime.utcnow()
        }

        if not fetch:
            # Return simple update
            return merge(result, {
                'progress': self.get_progress(obj.duration, view_offset)
            })

        # Retrieve session
        # Retrieve metadata and guid
        p_metadata, guid = self.get_metadata(rating_key)

        if not p_metadata:
            log.warn('Unable to retrieve metadata for rating_key %r', rating_key)
            return result

        if not guid or not guid.valid:
            return merge(result, {
                'duration': p_metadata.duration,
                'progress': self.get_progress(p_metadata.duration, view_offset)
            })

        try:
            # Create/Retrieve `Client` for session
            result['client'] = ClientManager.get.or_create({
                'key': info.get('machineIdentifier'),
                'title': info.get('client')
            }, fetch=True)

            # Create/Retrieve `User` for session
            result['user'] = UserManager.get.or_create({
                'key': to_integer(info.get('user_id')),
                'title': info.get('user_name')
            }, fetch=True)

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


class LSessionManager(Manager):
    get = GetLSession
    update = UpdateLSession

    model = Session
