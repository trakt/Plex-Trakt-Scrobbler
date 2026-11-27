from plugin.managers.core.base import Manager, Update
from plugin.models import TraktBasicCredential, TraktOAuthCredential
from plugin.models.core import db

from trakt import Trakt
import inspect
import logging

log = logging.getLogger(__name__)


class UpdateBasicCredential(Update):
    keys = ['password', 'token']

    def from_dict(self, basic_credential, changes, save=True):
        # Resolve `basic_credential`
        if inspect.isfunction(basic_credential):
            basic_credential = basic_credential()

        # Request new token on credential changes
        if 'username' in changes or 'password' in changes:
            # Retrieve credentials
            username = changes.get('username', basic_credential.account.username)
            password = changes.get('password', basic_credential.password)

            # Retrieve new token
            changes['token'] = Trakt['auth'].login(username, password)

        # Update `TraktBasicCredential`
        if not super(UpdateBasicCredential, self).from_dict(basic_credential, changes, save=save):
            return False

        return True


class TraktBasicCredentialManager(Manager):
    update = UpdateBasicCredential

    model = TraktBasicCredential

    @classmethod
    def delete(cls, *query, **kwargs):
        # Retrieve basic credential
        try:
            credential = cls.get(*query, **kwargs)
        except Exception as ex:
            log.warn('Unable to find basic credential (query: %r, kwargs: %r): %r', query, kwargs, ex)
            return False

        # Clear basic credential
        cls.update(credential, {
            'password': None,

            'token': None
        })

        return True


class UpdateOAuthCredential(Update):
    keys = ['code', 'access_token', 'refresh_token', 'created_at', 'expires_in', 'token_type', 'scope']

    def from_dict(self, oauth_credential, changes, save=True):
        # Update `TraktOAuthCredential`
        if not super(UpdateOAuthCredential, self).from_dict(oauth_credential, changes, save=save):
            return False

        return True


class TraktOAuthCredentialManager(Manager):
    update = UpdateOAuthCredential

    model = TraktOAuthCredential

    @classmethod
    def save_authorization(cls, oauth_credential, authorization, save=True):
        """
        Atomically replace OAuth credentials.

        Required complete response fields:
            access_token, refresh_token, token_type, expires_in, created_at, scope

        Scope is preserved exactly as returned by Trakt; it is not assumed.
        """
        required = ['access_token', 'refresh_token', 'token_type', 'expires_in', 'created_at', 'scope']
        missing = [key for key in required if key not in authorization]

        if missing:
            raise ValueError('Invalid OAuth response; missing fields: %s' % ','.join(missing))

        if not authorization.get('access_token'):
            raise ValueError('Invalid OAuth response; missing access_token')

        if not authorization.get('refresh_token'):
            raise ValueError('Invalid OAuth response; missing refresh_token')

        if not authorization.get('token_type'):
            raise ValueError('Invalid OAuth response; missing token_type')

        if authorization.get('created_at') is None:
            raise ValueError('Invalid OAuth response; missing created_at')

        if authorization.get('expires_in') is None:
            raise ValueError('Invalid OAuth response; missing expires_in')

        if authorization.get('scope') is None:
            raise ValueError('Invalid OAuth response; missing scope')

        data = {
            'access_token': authorization.get('access_token'),
            'refresh_token': authorization.get('refresh_token'),

            'created_at': authorization.get('created_at'),
            'expires_in': authorization.get('expires_in'),

            'token_type': authorization.get('token_type'),
            'scope': authorization.get('scope'),
        }

        # One save for all token fields. No partial access-token-only update.
        for key, value in data.items():
            setattr(oauth_credential, key, value)

        if save:
            with db.transaction():
                oauth_credential.save()

        return oauth_credential

    @classmethod
    def delete(cls, *query, **kwargs):
        # Retrieve oauth credential
        try:
            credential = cls.get(*query, **kwargs)
        except Exception as ex:
            log.warn('Unable to find oauth credential (query: %r, kwargs: %r): %r', query, kwargs, ex)
            return False

        # Clear oauth credential
        cls.update(credential, {
            'code': None,

            'access_token': None,
            'refresh_token': None,

            'created_at': None,
            'expires_in': None,

            'token_type': None,
            'scope': None
        })

        return True
