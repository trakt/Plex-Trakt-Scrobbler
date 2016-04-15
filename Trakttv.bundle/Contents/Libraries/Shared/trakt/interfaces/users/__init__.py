from trakt.interfaces.base import Interface
from trakt.mapper import CommentMapper, ListMapper

# Import child interfaces
from trakt.interfaces.users.lists import UsersListInterface, UsersListsInterface
from trakt.interfaces.users.settings import UsersSettingsInterface

import logging

log = logging.getLogger(__name__)

__all__ = [
    'UsersInterface',
    'UsersListsInterface',
    'UsersListInterface',
    'UsersSettingsInterface'
]


class UsersInterface(Interface):
    path = 'users'

    def likes(self, type=None, **kwargs):
        if type and type not in ['comments', 'lists']:
            raise ValueError('Unknown type specified: %r' % type)

        # Send request
        response = self.http.get('likes', params=[
            type
        ])

        if response.status_code < 200 or response.status_code >= 300:
            return

        # Parse response
        items = self.get_data(response, **kwargs)

        # Map items to comment/list objects
        for item in items:
            item_type = item.get('type')

            if item_type == 'comment':
                yield CommentMapper.comment(
                    self.client, item
                )
            elif item_type == 'list':
                yield ListMapper.custom_list(
                    self.client, item
                )
            else:
                log.warn('Unknown item returned, type: %r', item_type)
