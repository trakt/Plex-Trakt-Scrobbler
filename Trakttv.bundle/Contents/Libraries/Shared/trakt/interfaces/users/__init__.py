from trakt.interfaces.base import Interface

# Import child interfaces
from trakt.interfaces.users.settings import UsersSettingsInterface

__all__ = [
    'UsersInterface',
    'UsersSettingsInterface'
]


class UsersInterface(Interface):
    path = 'users'
