from trakt.interfaces.base import Interface

# Import child interfaces
from trakt.interfaces.users.lists import UsersListInterface, UsersListsInterface
from trakt.interfaces.users.settings import UsersSettingsInterface

__all__ = [
    'UsersInterface',
    'UsersListsInterface',
    'UsersListInterface',
    'UsersSettingsInterface'
]


class UsersInterface(Interface):
    path = 'users'
