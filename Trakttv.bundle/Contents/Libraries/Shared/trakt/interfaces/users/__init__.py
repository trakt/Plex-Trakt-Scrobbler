from __future__ import absolute_import, division, print_function

from trakt.core.helpers import popitems
from trakt.interfaces.base import Interface, authenticated
from trakt.mapper import CommentMapper, ListMapper

# Import child interfaces
from trakt.interfaces.users.lists import UsersListInterface, UsersListsInterface  # noqa: I100
from trakt.interfaces.users.settings import UsersSettingsInterface  # noqa: I100

import logging

log = logging.getLogger(__name__)

__all__ = (
    'UsersInterface',
    'UsersListsInterface',
    'UsersListInterface',
    'UsersSettingsInterface'
)


class UsersInterface(Interface):
    path = 'users'

    @authenticated
    def likes(self, type=None, **kwargs):
        if type and type not in ['comments', 'lists']:
            raise ValueError('Unknown type specified: %r' % type)

        if kwargs.get('parse') is False:
            raise ValueError('Parse can\'t be disabled on this method')

        # Send request
        response = self.http.get(
            'likes',
            params=[type],
            **popitems(kwargs, [
                'authenticated',
                'validate_token'
            ])
        )

        # Parse response
        items = self.get_data(response, **kwargs)

        if not items:
            return

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
