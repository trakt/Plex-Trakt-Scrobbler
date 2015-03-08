from plugin.core.helpers.variable import to_integer, merge
from plugin.managers.core.base import Manager, Get, Update
from plugin.managers.client import ClientManager
from plugin.managers.user import UserManager
from plugin.models import Session

from plex_metadata import Metadata, Guid
import apsw
import logging

log = logging.getLogger(__name__)


class GetLSession(Get):
    def __call__(self, info):
        machine_identifier = info.get('machineIdentifier')

        if not machine_identifier:
            return None

        return super(GetLSession, self).__call__(
            Session.session_key == 'l-%s' % machine_identifier
        )

    def or_create(self, info, fetch=False):
        machine_identifier = info.get('machineIdentifier')

        if not machine_identifier:
            return None

        try:
            # Create new session
            obj = self.manager.create(
                rating_key=to_integer(info.get('ratingKey')),
                session_key='l-%s' % machine_identifier,

                state='create'
            )

            # Update newly created object
            self.manager.update(obj, info, fetch)

            return obj
        except apsw.ConstraintError:
            # Return existing object
            return self(info)


class UpdateLSession(Update):
    def __call__(self, obj, info, fetch=False):
        data = self.to_dict(obj, info, fetch)

        return super(UpdateLSession, self).__call__(
            obj, data
        )

    def to_dict(self, obj, info, fetch=False):
        view_offset = to_integer(info.get('time'))
        rating_key = info.get('ratingKey')

        result = {
            'view_offset': view_offset
        }

        if not fetch:
            # Return simple update
            return merge(result, {
                'progress': self.get_progress(obj.duration, view_offset)
            })

        # Retrieve session
        # Retrieve metadata and guid
        p_metadata, p_guid = self.get_metadata(rating_key)

        if not p_metadata or not p_guid:
            log.warn('Unable to retrieve guid/metadata for session')
            return result

        # Store client + user in `result`
        result['client'] = ClientManager.get.or_create({
            'machine_identifier': info.get('machineIdentifier'),
            'title': info.get('client')
        }, fetch=True)

        result['user'] = UserManager.get.or_create({
            'id': to_integer(info.get('user_id')),
            'title': info.get('user_name')
        }, fetch=True)

        return merge(result, {
            # Pick account from `client` or `user` objects
            'account': self.get_account(result['client'], result['user']),

            'duration': p_metadata.duration,
            'progress': self.get_progress(p_metadata.duration, view_offset)
        })

    @staticmethod
    def get_account(client, user):
        if client and client.account_id:
            return client.account_id

        if user and user.account_id:
            return user.account_id

        return None

    @staticmethod
    def get_metadata(rating_key):
        # Retrieve metadata for `rating_key`
        try:
            metadata = Metadata.get(rating_key)
        except NotImplementedError, e:
            log.debug('%r, ignoring session', e.message)
            return None, None

        # Parse guid
        guid = Guid.parse(metadata.guid)

        return metadata, guid

    @staticmethod
    def get_progress(duration, view_offset):
        if duration is None:
            return None

        return round((float(view_offset) / duration) * 100, 2)


class LSessionManager(Manager):
    get = GetLSession
    update = UpdateLSession

    model = Session
