from plugin.managers.m_trakt import TraktAccountManager, TraktBasicCredentialManager, TraktOAuthCredentialManager

from plugin.managers.account import AccountManager
from plugin.managers.action import ActionManager
from plugin.managers.client import ClientManager
from plugin.managers.session import WSessionManager
from plugin.managers.user import UserManager

__all__ = [
    'TraktAccountManager',
    'TraktBasicCredentialManager', 'TraktOAuthCredentialManager',

    'AccountManager',
    'ActionManager',
    'ClientManager',
    'WSessionManager',
    'UserManager'
]
