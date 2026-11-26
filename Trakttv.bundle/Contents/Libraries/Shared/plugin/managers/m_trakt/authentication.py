# -*- coding: utf-8 -*-

"""
Trakt authentication manager.

Owns Trakt Device Code Flow and OAuth token lifecycle.

Design constraints:

- No Client Secret is used.
- Device authorization responses are temporary and are not persisted as account
  credentials.
- Refresh-token rotation is atomic: access token, refresh token, scope,
  token type, created_at and expiry are replaced together.
- Refreshes are serialized per account with a blocking lock. After acquiring
  the lock, latest persistent state is re-read so concurrent callers do not
  consume the same single-use refresh token twice.
- Network timeouts during refresh are not automatically retried with the old
  refresh token. A recovery/reauthorization path is exposed.
- Tokens, device codes, user codes and authorization payloads are never logged.
"""

from plugin.core.exceptions import AccountAuthenticationError
from plugin.managers.m_trakt.credential import TraktOAuthCredentialManager
from plugin.models import TraktAccount, TraktOAuthCredential

from trakt import Trakt

import calendar
import json
import logging
import requests
import threading
import time

log = logging.getLogger(__name__)


#
# Authentication states
#

AUTH_STATE_CONNECTED = 'connected'
AUTH_STATE_AUTHORIZATION_REQUIRED = 'authorization_required'
AUTH_STATE_AUTHORIZATION_IN_PROGRESS = 'authorization_in_progress'
AUTH_STATE_AUTHENTICATION_ERROR = 'authentication_error'


#
# Device Code Flow endpoints
#

DEVICE_CODE_PATH = 'oauth/device/code'
DEVICE_TOKEN_PATH = 'oauth/device/token'
TOKEN_PATH = 'oauth/token'
USER_SETTINGS_PATH = 'users/settings'


#
# Errors
#

class TraktAuthenticationError(Exception):
    """Base Trakt authentication error."""


class TraktConfigurationError(TraktAuthenticationError):
    """Application configuration problem, e.g. missing/invalid Client ID."""


class TraktAPIError(TraktAuthenticationError):
    """Trakt API returned a non-success response. Preserves response body."""

    def __init__(self, message, status_code=None, body=None, headers=None, response=None):
        super(TraktAPIError, self).__init__(message)

        self.message = message
        self.status_code = status_code
        self.body = body
        self.headers = headers or {}
        self.response = response

    def __str__(self):
        return self.message

    def __repr__(self):
        return 'TraktAPIError(status_code=%r, body=%r)' % (
            self.status_code,
            self.body,
        )


class TraktNetworkError(TraktAuthenticationError):
    """Network/timeout error while contacting Trakt."""


class DeviceAuthorizationError(TraktAuthenticationError):
    """Base Device Code Flow error."""


class AuthorizationPending(DeviceAuthorizationError):
    """User has not authorized yet."""


class SlowDown(DeviceAuthorizationError):
    """Polling too quickly; increase interval."""


class DeviceCodeExpired(DeviceAuthorizationError):
    """Device code expired; request a new one."""


class AuthorizationDenied(DeviceAuthorizationError):
    """User denied authorization."""


class InvalidDeviceCode(DeviceAuthorizationError):
    """Device code invalid."""


class TokenRefreshError(TraktAuthenticationError):
    """Token refresh failed."""


class TokenRefreshRejected(TokenRefreshError, AccountAuthenticationError):
    """Refresh token rejected; account requires reauthorization."""


class InvalidClient(TraktConfigurationError, TokenRefreshError):
    """invalid_client: application configuration problem."""


class RateLimitError(TraktAPIError):
    """HTTP 429; respect Retry-After / rate-limit instructions."""

    def __init__(self, message, retry_after=None, status_code=429, body=None, headers=None, response=None):
        super(RateLimitError, self).__init__(
            message,
            status_code=status_code,
            body=body,
            headers=headers,
            response=response,
        )

        self.message = message
        self.retry_after = retry_after


class TokenRefreshUncertainError(TokenRefreshError):
    """
    Network timeout/lost response during refresh.

    Trakt may have consumed the old refresh token and returned its replacement,
    but the response was lost. Do not automatically retry the old token. Recovery
    requires checking persistent storage or reauthorizing the account.
    """

    def __init__(self, message, account_key=None):
        super(TokenRefreshUncertainError, self).__init__(message)

        self.message = message
        self.account_key = account_key


class TraktAuthorizationRequired(TokenRefreshError, AccountAuthenticationError):
    """Account requires Device Code reauthorization."""


#
# Constants
#

DEFAULT_BASE_URL = 'https://api.trakt.tv'
DEFAULT_TIMEOUT = (6.05, 24)

DEFAULT_DEVICE_INTERVAL = 5
DEFAULT_DEVICE_EXPIRES_IN = 600

# Refresh before expiry. The bundled trakt.py uses a 48-hour safety window;
# stay compatible with it while also not starting requests at the edge.
TOKEN_EXPIRY_MARGIN_SECONDS = 48 * 60 * 60 + 300

REQUIRED_AUTHORIZATION_FIELDS = (
    'access_token',
    'refresh_token',
    'token_type',
    'expires_in',
    'created_at',
    'scope',
)


class TraktAuthenticationManager(object):
    """
    Trakt Authentication Manager.

    Suggested responsibilities:

        request_device_code()
        poll_device_token()
        authenticate_account()
        get_user_settings()
        save_authorization()
        refresh_access_token()
        ensure_valid_token()

    The class can be used as a singleton in the Plex plugin; methods also accept
    explicit `client_id`, `base_url`, `session`, and `timeout` for testing.
    """

    _default_client_id = None
    _default_base_url = None
    _default_timeout = DEFAULT_TIMEOUT
    _default_session = None

    _refresh_locks = {}
    _refresh_locks_guard = threading.Lock()

    #
    # Configuration
    #

    @classmethod
    def configure(cls, client_id=None, base_url=None, timeout=None, session=None):
        """Configure defaults used by plugin integration. No Client Secret."""
        if client_id is not None:
            cls._default_client_id = client_id

        if base_url is not None:
            cls._default_base_url = base_url

        if timeout is not None:
            cls._default_timeout = timeout

        if session is not None:
            cls._default_session = session

        return cls

    @classmethod
    def get_client_id(cls, client_id=None):
        return cls._resolve_client_id(client_id)

    #
    # Device Code Flow
    #

    @classmethod
    def request_device_code(cls, client_id=None, base_url=None, session=None, timeout=None):
        """
        POST /oauth/device/code

        Sends only Client ID. Returns temporary device authorization state.
        Nothing here is persisted as account credentials.
        """
        client_id = cls._require_client_id(client_id)

        response = cls._http_post(
            cls._endpoint(base_url, DEVICE_CODE_PATH),
            {
                'client_id': client_id,
            },
            client_id=client_id,
            session=session,
            timeout=timeout,
        )

        if not isinstance(response, dict):
            raise DeviceAuthorizationError('Invalid device code response')

        # Preserve Trakt fields; `verification_url` must come from Trakt.
        # Do not construct old /pin/{app_id} URLs.
        if not response.get('device_code'):
            raise DeviceAuthorizationError('Device code response missing device_code')

        if not response.get('user_code'):
            raise DeviceAuthorizationError('Device code response missing user_code')

        verification_url = response.get('verification_url') or response.get('verification_uri')

        if not verification_url:
            raise DeviceAuthorizationError('Device code response missing verification_url')

        # Normalize common fields while preserving original data.
        result = dict(response)
        result['verification_url'] = verification_url
        result['expires_in'] = _safe_int(response.get('expires_in'), DEFAULT_DEVICE_EXPIRES_IN)
        result['interval'] = _safe_int(response.get('interval'), DEFAULT_DEVICE_INTERVAL)

        return result

    @classmethod
    def format_device_instructions(cls, device_authorization):
        """
        Connect Trakt

            1. Open: [verification_url]
            2. Enter code: ABCD-EFGH

            Waiting for authorization...
        """
        verification_url = (
            device_authorization.get('verification_url') or
            device_authorization.get('verification_uri') or
            ''
        )
        user_code = device_authorization.get('user_code') or ''

        return (
            'Connect Trakt\n'
            '1. Open: %s\n'
            '2. Enter code: %s\n'
            'Waiting for authorization...'
        ) % (verification_url, user_code)

    @classmethod
    def poll_device_token(
        cls,
        device_code,
        client_id=None,
        interval=None,
        expires_in=None,
        base_url=None,
        session=None,
        timeout=None,
        sleep=None,
        now=None,
        max_network_retries=3,
    ):
        """
        POST /oauth/device/token until authorized.

        Sends device_code + Client ID. No Client Secret.

        Handles:
            authorization_pending -> wait `interval`, retry
            slow_down             -> increase polling interval
            expired_token         -> raise DeviceCodeExpired
            access_denied         -> raise AuthorizationDenied
            network errors        -> retry cautiously, never faster than interval
        """
        if not device_code:
            raise InvalidDeviceCode('device_code is required')

        client_id = cls._require_client_id(client_id)

        sleep = sleep or time.sleep
        now = now or time.time

        poll_interval = _safe_int(interval, DEFAULT_DEVICE_INTERVAL)
        if poll_interval < 1:
            poll_interval = 1

        expires_in = _safe_int(expires_in, DEFAULT_DEVICE_EXPIRES_IN)
        deadline = now() + expires_in

        network_failures = 0

        while True:
            if now() >= deadline:
                raise DeviceCodeExpired('Device code expired; request another code')

            try:
                response = cls._http_post(
                    cls._endpoint(base_url, DEVICE_TOKEN_PATH),
                    {
                        'device_code': device_code,
                        'client_id': client_id,
                    },
                    client_id=client_id,
                    session=session,
                    timeout=timeout,
                )
            except TraktAPIError as ex:
                error = _error_code(ex.body)

                # Authorization pending / slow down are polling states.
                if _is_authorization_pending(ex, error):
                    sleep(poll_interval)
                    continue

                if _is_slow_down(ex, error):
                    poll_interval += 1
                    sleep(poll_interval)
                    continue

                if _is_expired_token(ex, error):
                    raise DeviceCodeExpired('Device code expired; request another code')

                if _is_access_denied(ex, error):
                    raise AuthorizationDenied('User denied Trakt authorization')

                if ex.status_code == 429:
                    retry_after = _retry_after(ex.headers)
                    sleep(_safe_int(retry_after, poll_interval))
                    continue

                if _is_invalid_client(ex, error):
                    raise InvalidClient('invalid_client: check Trakt Client ID')

                # Unknown API error: preserve body in exception; don't spin.
                raise
            except TraktNetworkError:
                network_failures += 1

                if network_failures > max_network_retries:
                    raise

                # Retry appropriately, but never poll faster than `interval`.
                sleep(poll_interval)
                continue

            if isinstance(response, dict) and response.get('access_token'):
                # Complete response validation happens in `_normalize_authorization`.
                authorization = cls._normalize_authorization(response)
                return authorization

            # Unexpected success without token; wait and retry until expiry.
            sleep(poll_interval)

    @classmethod
    def authenticate_account(
        cls,
        t_account,
        device_authorization=None,
        client_id=None,
        base_url=None,
        session=None,
        timeout=None,
        on_device_code=None,
        on_status=None,
        sleep=None,
        now=None,
        max_expired_retries=1,
    ):
        """
        Complete Device Code Flow and associate authorization with existing account.

        Existing `TraktAccount`, Plex association, watched state and sync
        preferences are preserved. Only OAuth credential + auth state changes.
        """
        account_key = cls._account_key(t_account)

        _set_auth_state(t_account, AUTH_STATE_AUTHORIZATION_IN_PROGRESS)
        _emit_status(on_status, 'waiting_for_authorization', account_key=account_key)

        log.info('[Trakt] Device authorization initiated')

        expired_retries = 0

        try:
            if device_authorization is None:
                device_authorization = cls.request_device_code(
                    client_id=client_id,
                    base_url=base_url,
                    session=session,
                    timeout=timeout,
                )

            while True:
                _emit_device_code(on_device_code, device_authorization)
                log.info('[Trakt] Waiting for user authorization')

                try:
                    authorization = cls.poll_device_token(
                        device_authorization.get('device_code'),
                        client_id=client_id,
                        interval=device_authorization.get('interval'),
                        expires_in=device_authorization.get('expires_in'),
                        base_url=base_url,
                        session=session,
                        timeout=timeout,
                        sleep=sleep,
                        now=now,
                    )
                    break
                except DeviceCodeExpired:
                    if expired_retries >= max_expired_retries:
                        raise

                    expired_retries += 1
                    log.info('[Trakt] Device code expired; requesting another code')

                    device_authorization = cls.request_device_code(
                        client_id=client_id,
                        base_url=base_url,
                        session=session,
                        timeout=timeout,
                    )

            settings = cls.get_user_settings(
                authorization['access_token'],
                client_id=client_id,
                base_url=base_url,
                session=session,
                timeout=timeout,
            )

            cls.save_authorization(
                t_account,
                authorization,
                settings=settings,
            )

            username = _extract_username(settings)
            log.info('[Trakt] Account authorized: %s', username or 'unknown')
            _emit_status(on_status, 'authorized', account_key=account_key, username=username)

            return t_account

        except AuthorizationDenied:
            _set_auth_state(t_account, AUTH_STATE_AUTHORIZATION_REQUIRED)
            log.info('[Trakt] Account requires reauthorization')
            raise
        except TraktConfigurationError:
            _set_auth_state(t_account, AUTH_STATE_AUTHENTICATION_ERROR)
            raise
        except DeviceCodeExpired:
            _set_auth_state(t_account, AUTH_STATE_AUTHORIZATION_REQUIRED)
            raise
        except TraktNetworkError:
            _set_auth_state(t_account, AUTH_STATE_AUTHENTICATION_ERROR)
            raise
        except TraktAuthenticationError:
            _set_auth_state(t_account, AUTH_STATE_AUTHENTICATION_ERROR)
            raise
        except Exception:
            _set_auth_state(t_account, AUTH_STATE_AUTHENTICATION_ERROR)
            raise

    @classmethod
    def authenticate_account_with_device(
        cls,
        t_account,
        device_authorization,
        client_id=None,
        base_url=None,
        session=None,
        timeout=None,
        sleep=None,
        now=None,
    ):
        """Poll an already displayed device authorization and save account."""
        return cls.authenticate_account(
            t_account,
            device_authorization=device_authorization,
            client_id=client_id,
            base_url=base_url,
            session=session,
            timeout=timeout,
            sleep=sleep,
            now=now,
        )

    #
    # Trakt account identification / persistence
    #

    @classmethod
    def get_user_settings(cls, access_token, client_id=None, base_url=None, session=None, timeout=None):
        """GET /users/settings with Bearer access token."""
        if not access_token:
            raise TraktAuthorizationRequired('Access token is required')

        response = cls._http_get(
            cls._endpoint(base_url, USER_SETTINGS_PATH),
            access_token=access_token,
            client_id=client_id,
            session=session,
            timeout=timeout,
        )

        if not isinstance(response, dict) or not response:
            raise TraktAuthenticationError('Unable to retrieve account details for token')

        return response

    @classmethod
    def save_authorization(cls, t_account, authorization, settings=None, username=None):
        """
        Persist complete OAuth response atomically.

        Existing account record / Plex association is not replaced.
        """
        authorization = cls._normalize_authorization(authorization)

        account_id = cls._account_id(t_account)

        oauth = _reload_oauth_credential(account_id)

        if oauth is None:
            oauth = TraktOAuthCredential(account=t_account)

        TraktOAuthCredentialManager.save_authorization(
            oauth,
            authorization,
        )

        resolved_username = username or _extract_username(settings)

        # Re-fetch account to avoid clobbering unrelated fields.
        account = _reload_account(account_id) or t_account

        if resolved_username:
            account.username = resolved_username

        account.auth_state = AUTH_STATE_CONNECTED
        account.save()

        log.info('[Trakt] Credentials persisted')
        return account

    #
    # Token refresh / atomic rotation
    #

    @classmethod
    def ensure_valid_token(cls, t_account, oauth_credential=None, now=None, client_id=None, base_url=None, session=None, timeout=None):
        """
        Return a valid `TraktOAuthCredential`, refreshing once if needed.

        Called before authenticated scrobbling/sync requests. Existing callers
        do not need to know whether token came from old OAuth or Device Flow.
        """
        account_key = cls._account_key(t_account)
        credential = oauth_credential or _reload_oauth_credential(cls._account_id(t_account))

        if credential is None or not credential.access_token:
            _set_auth_state(t_account, AUTH_STATE_AUTHORIZATION_REQUIRED)
            log.info('[Trakt] Account requires reauthorization')
            raise TraktAuthorizationRequired('Trakt account has no OAuth credentials; reauthorization required')

        if _is_access_token_valid(credential, now=now):
            return credential

        # Legacy/invalid accounts require explicit reauthorization.
        account = _reload_account(cls._account_id(t_account)) or t_account
        if getattr(account, 'auth_state', None) == AUTH_STATE_AUTHORIZATION_REQUIRED:
            raise TraktAuthorizationRequired('Account requires reauthorization')

        return cls.refresh_access_token(
            t_account,
            oauth_credential=credential,
            client_id=client_id,
            base_url=base_url,
            session=session,
            timeout=timeout,
        )

    @classmethod
    def refresh_access_token(cls, t_account, oauth_credential=None, client_id=None, base_url=None, session=None, timeout=None, now=None):
        """
        Refresh token with per-account locking and atomic rotation.

        Sequence:
            1. Acquire per-account refresh lock.
            2. Read latest refresh token from persistent storage.
            3. Send refresh request (no Client Secret).
            4. Validate complete response.
            5. Atomically replace access token, refresh token, expiry metadata.
            6. Release lock.

        No automatic retry of a possibly consumed refresh token on timeout.
        """
        account_key = cls._account_key(t_account)
        account_id = cls._account_id(t_account)
        lock = cls._refresh_lock(account_key)

        # Capture pre-lock token to detect another thread completing refresh.
        before = oauth_credential or _reload_oauth_credential(account_id)
        original_refresh_token = before.refresh_token if before else None

        with lock:
            # Re-read latest persistent state inside lock.
            credential = _reload_oauth_credential(account_id) or before

            if credential is None:
                _set_auth_state(t_account, AUTH_STATE_AUTHORIZATION_REQUIRED)
                raise TraktAuthorizationRequired('No OAuth credential; reauthorization required')

            latest_refresh_token = credential.refresh_token

            # Another thread refreshed while we waited; use newly stored token.
            if (
                original_refresh_token and
                latest_refresh_token != original_refresh_token and
                _is_access_token_valid(credential, now=now)
            ):
                return _reload_oauth_credential(account_id) or credential

            # Re-check validity after acquiring lock.
            if _is_access_token_valid(credential, now=now):
                return credential

            account = _reload_account(account_id) or t_account
            if getattr(account, 'auth_state', None) == AUTH_STATE_AUTHORIZATION_REQUIRED:
                raise TraktAuthorizationRequired('Account requires reauthorization')

            if not latest_refresh_token:
                _set_auth_state(t_account, AUTH_STATE_AUTHORIZATION_REQUIRED)
                log.info('[Trakt] Refresh rejected: missing refresh token')
                raise TraktAuthorizationRequired('Missing refresh token; reauthorization required')

            client_id = cls._require_client_id(client_id)

            payload = {
                'refresh_token': latest_refresh_token,
                'client_id': client_id,
                'grant_type': 'refresh_token',
            }

            try:
                response = cls._http_post(
                    cls._endpoint(base_url, TOKEN_PATH),
                    payload,
                    client_id=client_id,
                    session=session,
                    timeout=timeout,
                )
            except TraktNetworkError as ex:
                # Do not automatically retry old token. Recovery requires
                # checking persistent storage or reauthorization.
                _set_auth_state(t_account, AUTH_STATE_AUTHENTICATION_ERROR)
                log.warn('[Trakt] Refresh outcome unknown; recovery required')
                raise TokenRefreshUncertainError(
                    'Refresh request timed out; token may have been consumed; recover or reauthorize',
                    account_key=account_key,
                )
            except TraktAPIError as ex:
                error = _error_code(ex.body)

                if _is_invalid_client(ex, error):
                    _set_auth_state(t_account, AUTH_STATE_AUTHENTICATION_ERROR)
                    log.info('[Trakt] invalid_client: check Trakt Client ID')
                    raise InvalidClient('invalid_client: check Trakt Client ID')

                if _is_rate_limited(ex):
                    _set_auth_state(t_account, AUTH_STATE_AUTHENTICATION_ERROR)
                    raise RateLimitError(
                        'Trakt rate limit exceeded; respect Retry-After',
                        retry_after=_retry_after(ex.headers),
                        status_code=ex.status_code or 429,
                        body=ex.body,
                        headers=ex.headers,
                        response=ex.response,
                    )

                if _is_invalid_grant(ex, error) or _is_session_not_found(ex, error):
                    _set_auth_state(t_account, AUTH_STATE_AUTHORIZATION_REQUIRED)
                    log.info('[Trakt] Refresh rejected: %s', error or 'invalid_grant')
                    _emit_refresh_rejected(t_account, error or 'invalid_grant')
                    raise TokenRefreshRejected(
                        'Refresh token rejected; reauthorization required'
                    )

                _set_auth_state(t_account, AUTH_STATE_AUTHENTICATION_ERROR)
                raise TokenRefreshError(
                    'Token refresh failed; existing account state left intact'
                )

            try:
                authorization = cls._normalize_authorization(response)
            except TraktAuthenticationError:
                _set_auth_state(t_account, AUTH_STATE_AUTHENTICATION_ERROR)
                raise TokenRefreshError('Invalid token refresh response; credentials not rotated')

            # Atomic replace: access_token + refresh_token + expiry metadata.
            TraktOAuthCredentialManager.save_authorization(
                credential,
                authorization,
            )

            account = _reload_account(account_id) or t_account
            account.auth_state = AUTH_STATE_CONNECTED
            account.save()

            log.info('[Trakt] Access token refreshed')
            _emit_refresh(t_account, authorization)

            return _reload_oauth_credential(account_id) or credential

    @classmethod
    def recover_uncertain_refresh(cls, t_account, client_id=None, base_url=None, session=None, timeout=None):
        """
        Recovery path for timeout-after-refresh.

        Re-reads persistent storage. If a replacement refresh token was already
        saved, use it. Do not retry the old token blindly. Otherwise require
        reauthorization.
        """
        account_id = cls._account_id(t_account)
        credential = _reload_oauth_credential(account_id)

        if credential and _is_access_token_valid(credential):
            account = _reload_account(account_id) or t_account
            account.auth_state = AUTH_STATE_CONNECTED
            account.save()
            return credential

        # Do not retry the old token blindly. Recovery requires reauthorization
        # unless persistent storage already contains a valid replacement.
        _set_auth_state(t_account, AUTH_STATE_AUTHORIZATION_REQUIRED)
        raise TraktAuthorizationRequired('Recovery requires reauthorization')

    @classmethod
    def reauthorize_account(cls, t_account, **kwargs):
        """Start Device Code Flow for existing account; preserve associations."""
        return cls.authenticate_account(t_account, **kwargs)

    #
    # Authorization validation / normalization
    #

    @classmethod
    def _normalize_authorization(cls, authorization):
        if not isinstance(authorization, dict):
            raise TraktAuthenticationError('Invalid OAuth response: expected object')

        missing = [
            field for field in REQUIRED_AUTHORIZATION_FIELDS
            if field not in authorization
        ]

        if missing:
            raise TraktAuthenticationError(
                'Invalid OAuth response: missing fields %s' % ','.join(missing)
            )

        access_token = authorization.get('access_token')
        refresh_token = authorization.get('refresh_token')
        token_type = authorization.get('token_type')
        scope = authorization.get('scope')

        if not access_token:
            raise TraktAuthenticationError('Invalid OAuth response: missing access_token')

        if not refresh_token:
            raise TraktAuthenticationError('Invalid OAuth response: missing refresh_token')

        if not token_type:
            raise TraktAuthenticationError('Invalid OAuth response: missing token_type')

        created_at = _safe_int(authorization.get('created_at'), None)
        expires_in = _safe_int(authorization.get('expires_in'), None)

        if created_at is None:
            raise TraktAuthenticationError('Invalid OAuth response: invalid created_at')

        if expires_in is None or expires_in < 0:
            raise TraktAuthenticationError('Invalid OAuth response: invalid expires_in')

        # Preserve exact scope returned by Trakt; do not assume.
        if scope is None:
            raise TraktAuthenticationError('Invalid OAuth response: missing scope')

        return {
            'access_token': access_token,
            'refresh_token': refresh_token,
            'token_type': token_type,
            'expires_in': expires_in,
            'created_at': created_at,
            'scope': scope,
        }

    #
    # HTTP
    #

    @classmethod
    def _http_post(cls, url, payload, client_id=None, session=None, timeout=None):
        headers = {
            'Content-Type': 'application/json',
            'trakt-api-version': '2',
        }

        if client_id:
            headers['trakt-api-key'] = client_id

        body = json.dumps(payload)

        try:
            http_session = session or cls._default_session

            if http_session is not None:
                response = http_session.post(
                    url,
                    data=body,
                    headers=headers,
                    timeout=cls._resolve_timeout(timeout),
                )
            else:
                response = requests.post(
                    url,
                    data=body,
                    headers=headers,
                    timeout=cls._resolve_timeout(timeout),
                )
        except requests.exceptions.Timeout as ex:
            raise TraktNetworkError('Trakt request timed out')
        except requests.exceptions.RequestException as ex:
            raise TraktNetworkError('Trakt request failed: %s' % _safe_error(ex))
        except Exception as ex:
            raise TraktNetworkError('Trakt request failed: %s' % _safe_error(ex))

        return cls._response_or_raise(response)

    @classmethod
    def _http_get(cls, url, access_token=None, client_id=None, session=None, timeout=None):
        headers = {
            'trakt-api-version': '2',
        }

        if client_id:
            headers['trakt-api-key'] = client_id

        if access_token:
            headers['Authorization'] = 'Bearer %s' % access_token

        try:
            http_session = session or cls._default_session

            if http_session is not None:
                response = http_session.get(
                    url,
                    headers=headers,
                    timeout=cls._resolve_timeout(timeout),
                )
            else:
                response = requests.get(
                    url,
                    headers=headers,
                    timeout=cls._resolve_timeout(timeout),
                )
        except requests.exceptions.Timeout:
            raise TraktNetworkError('Trakt request timed out')
        except requests.exceptions.RequestException as ex:
            raise TraktNetworkError('Trakt request failed: %s' % _safe_error(ex))
        except Exception as ex:
            raise TraktNetworkError('Trakt request failed: %s' % _safe_error(ex))

        return cls._response_or_raise(response)

    @classmethod
    def _response_or_raise(cls, response):
        status_code = getattr(response, 'status_code', None)
        headers = getattr(response, 'headers', {}) or {}
        body = _parse_body(response)

        if status_code is not None and (status_code < 200 or status_code >= 300):
            if status_code == 429:
                raise RateLimitError(
                    'Trakt rate limit exceeded; respect Retry-After',
                    retry_after=_retry_after(headers),
                    status_code=status_code,
                    body=body,
                    headers=headers,
                    response=response,
                )

            raise TraktAPIError(
                'Trakt API error %s' % status_code,
                status_code=status_code,
                body=body,
                headers=headers,
                response=response,
            )

        return body

    #
    # Client resolution
    #

    @classmethod
    def _require_client_id(cls, client_id=None):
        client_id = cls._resolve_client_id(client_id)

        if not client_id:
            raise TraktConfigurationError(
                'invalid_client: Trakt Client ID is not configured ([trakt] client_id)'
            )

        return client_id

    @classmethod
    def _resolve_client_id(cls, client_id=None):
        if client_id:
            return client_id

        if cls._default_client_id:
            return cls._default_client_id

        try:
            value = Trakt.configuration['client.id']
        except Exception:
            value = None

        return value or None

    @classmethod
    def _resolve_base_url(cls, base_url=None):
        if base_url:
            return base_url.rstrip('/')

        if cls._default_base_url:
            return cls._default_base_url.rstrip('/')

        try:
            value = Trakt.base_url
        except Exception:
            value = None

        return (value or DEFAULT_BASE_URL).rstrip('/')

    @classmethod
    def _resolve_timeout(cls, timeout=None):
        if timeout is not None:
            return timeout

        return cls._default_timeout or DEFAULT_TIMEOUT

    @classmethod
    def _endpoint(cls, base_url, path):
        return '%s/%s' % (cls._resolve_base_url(base_url), path.lstrip('/'))

    #
    # Locking / account helpers
    #

    @classmethod
    def _refresh_lock(cls, account_key):
        key = account_key or '__unknown__'

        with cls._refresh_locks_guard:
            if key not in cls._refresh_locks:
                cls._refresh_locks[key] = threading.RLock()

            return cls._refresh_locks[key]

    @classmethod
    def _account_key(cls, t_account):
        account_id = cls._account_id(t_account)

        if account_id is not None:
            return 'id:%s' % account_id

        username = getattr(t_account, 'username', None)

        if username:
            return 'username:%s' % username

        return 'unknown'

    @classmethod
    def _account_id(cls, t_account):
        if isinstance(t_account, TraktAccount):
            return t_account.id

        return t_account


#
# Helpers
#

def _set_auth_state(t_account, state):
    try:
        account = _reload_account(_account_id_of(t_account)) or t_account
        account.auth_state = state
        account.save()
    except Exception:
        # Never let auth-state bookkeeping hide original auth error.
        log.warn('[Trakt] Unable to persist auth state', exc_info=True)


def _account_id_of(t_account):
    if isinstance(t_account, TraktAccount):
        return t_account.id

    return t_account


def _reload_account(account_id):
    if account_id is None:
        return None

    try:
        return TraktAccount.select().where(TraktAccount.id == account_id).first()
    except Exception:
        return None


def _reload_oauth_credential(account_id):
    if account_id is None:
        return None

    try:
        return (
            TraktOAuthCredential
            .select()
            .where(TraktOAuthCredential.account == account_id)
            .first()
        )
    except Exception:
        return None


def _is_access_token_valid(credential, now=None, margin=TOKEN_EXPIRY_MARGIN_SECONDS):
    if credential is None or not credential.access_token:
        return False

    created_at = _safe_int(getattr(credential, 'created_at', None), None)
    expires_in = _safe_int(getattr(credential, 'expires_in', None), None)

    if created_at is None or expires_in is None:
        return False

    current = _safe_int(now, None)

    if current is None:
        current = int(calendar.timegm(time.gmtime()))

    expires_at = created_at + expires_in

    return current + margin < expires_at


def _safe_int(value, default=None):
    if value is None:
        return default

    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _parse_body(response):
    # Prefer JSON; preserve raw body for failed token exchanges.
    try:
        return response.json()
    except Exception:
        pass

    try:
        text = getattr(response, 'text', None)
    except Exception:
        text = None

    if text is None:
        try:
            text = getattr(response, 'content', None)
        except Exception:
            text = None

    if text is None:
        return None

    try:
        return json.loads(text)
    except Exception:
        return text


def _error_code(body):
    if isinstance(body, dict):
        return body.get('error') or body.get('error_code') or body.get('code')

    if isinstance(body, basestring):
        # Preserve body; attempt to extract error from raw text.
        try:
            parsed = json.loads(body)
            if isinstance(parsed, dict):
                return parsed.get('error') or parsed.get('error_code') or parsed.get('code')
        except Exception:
            pass

        return body

    return None


def _is_authorization_pending(ex, error):
    return error == 'authorization_pending'


def _is_slow_down(ex, error):
    return error == 'slow_down'


def _is_expired_token(ex, error):
    return error in ('expired_token', 'expired', 'invalid_device_code', 'device_code_expired') or (
        ex.status_code == 400 and error == 'invalid_grant' and _body_contains(ex.body, 'expired')
    )


def _is_access_denied(ex, error):
    return error in ('access_denied', 'authorization_denied', 'user_denied', 'denied')


def _is_invalid_client(ex, error):
    return error == 'invalid_client' or ex.status_code == 401 and error in (None, '', 'invalid_client')


def _is_invalid_grant(ex, error):
    return error == 'invalid_grant' or _is_session_not_found(ex, error)


def _is_session_not_found(ex, error):
    if error and 'session not found' in str(error).lower():
        return True

    if ex.body and 'session not found' in str(ex.body).lower():
        return True

    return False


def _is_rate_limited(ex):
    return ex.status_code == 429


def _retry_after(headers):
    if not headers:
        return None

    for key in ('Retry-After', 'retry-after', 'retry_after', 'X-RateLimit-Retry-After', 'x-ratelimit-retry-after'):
        if key in headers:
            return headers.get(key)

    return None


def _body_contains(body, needle):
    return needle in str(body).lower()


def _safe_error(ex):
    # Don't include response body in network error logs; preserve type.
    return ex.__class__.__name__


def _extract_username(settings):
    if not isinstance(settings, dict):
        return None

    user = settings.get('user') or {}

    return user.get('username')


def _emit_status(callback, status, **kwargs):
    if callback is None:
        return

    try:
        callback(status, **kwargs)
    except Exception:
        log.warn('[Trakt] Status callback failed', exc_info=True)


def _emit_device_code(callback, device_authorization):
    if callback is None:
        return

    try:
        callback(device_authorization)
    except Exception:
        log.warn('[Trakt] Device-code callback failed', exc_info=True)


def _emit_refresh(account, authorization):
    try:
        username = getattr(account, 'username', None)
        if not username:
            username = _account_id_of(account)

        Trakt.emit(
            'oauth.refresh',
            username,
            authorization,
            __suppress=True,
        )
    except Exception:
        log.warn('[Trakt] oauth.refresh callback failed', exc_info=True)


def _emit_refresh_rejected(account, reason):
    try:
        username = getattr(account, 'username', None)
        if not username:
            username = _account_id_of(account)

        Trakt.emit(
            'oauth.refresh.rejected',
            username,
            reason,
            __suppress=True,
        )
    except Exception:
        log.warn('[Trakt] oauth.refresh.rejected callback failed', exc_info=True)


# Python 2 compatibility
try:
    basestring
except NameError:
    basestring = str
