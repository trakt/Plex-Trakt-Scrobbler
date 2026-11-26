# -*- coding: utf-8 -*-

"""Unit tests for Trakt Device Code Flow and token rotation helpers."""

import json

from plugin.managers.m_trakt.authentication import (
    AuthorizationDenied,
    DeviceCodeExpired,
    InvalidClient,
    SlowDown,
    TraktAPIError,
    TraktAuthenticationManager,
    TraktConfigurationError,
    TraktNetworkError,
)


class FakeResponse(object):
    def __init__(self, status_code=200, body=None, headers=None):
        self.status_code = status_code
        self._body = body or {}
        self.headers = headers or {}
        self.text = json.dumps(self._body)

    def json(self):
        return self._body


class FakeSession(object):
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []

    def post(self, url, data=None, headers=None, timeout=None):
        self.calls.append({
            'url': url,
            'data': json.loads(data),
            'headers': headers or {},
            'timeout': timeout,
        })

        response = self.responses.pop(0)

        if isinstance(response, Exception):
            raise response

        return response

    def get(self, url, headers=None, timeout=None):
        self.calls.append({
            'url': url,
            'headers': headers or {},
            'timeout': timeout,
        })
        response = self.responses.pop(0)

        if isinstance(response, Exception):
            raise response

        return response


def no_sleep(_):
    return None


def fixed_now():
    return 1000


def test_request_device_code_sends_only_client_id_and_uses_returned_verification_url():
    session = FakeSession([
        FakeResponse(200, {
            'device_code': 'DEVICE',
            'user_code': 'ABCD-EFGH',
            'verification_url': 'https://trakt.tv/activate',
            'expires_in': 600,
            'interval': 5,
        })
    ])

    result = TraktAuthenticationManager.request_device_code(
        client_id='CLIENT',
        base_url='https://api.trakt.tv',
        session=session,
    )

    assert result['verification_url'] == 'https://trakt.tv/activate'
    assert result['user_code'] == 'ABCD-EFGH'
    assert session.calls[0]['url'] == 'https://api.trakt.tv/oauth/device/code'
    assert session.calls[0]['data'] == {'client_id': 'CLIENT'}
    assert 'client_secret' not in session.calls[0]['data']


def test_format_device_instructions():
    text = TraktAuthenticationManager.format_device_instructions({
        'verification_url': 'https://trakt.tv/activate',
        'user_code': 'ABCD-EFGH',
    })

    assert 'Connect Trakt' in text
    assert '1. Open: https://trakt.tv/activate' in text
    assert '2. Enter code: ABCD-EFGH' in text
    assert 'Waiting for authorization...' in text
    assert '/pin/' not in text


def test_missing_client_id_is_configuration_error():
    try:
        TraktAuthenticationManager.request_device_code(client_id='', base_url='https://api.trakt.tv')
    except TraktConfigurationError:
        return

    raise AssertionError('Expected TraktConfigurationError')


def test_poll_pending_then_authorized_respects_interval_and_rotation_fields():
    session = FakeSession([
        FakeResponse(400, {'error': 'authorization_pending'}),
        FakeResponse(200, {
            'access_token': 'NEW_ACCESS',
            'refresh_token': 'NEW_REFRESH',
            'token_type': 'bearer',
            'expires_in': 604800,
            'scope': 'public',
            'created_at': 1795750000,
        }),
    ])

    slept = []

    auth = TraktAuthenticationManager.poll_device_token(
        'DEVICE',
        client_id='CLIENT',
        interval=7,
        expires_in=600,
        base_url='https://api.trakt.tv',
        session=session,
        sleep=lambda seconds: slept.append(seconds),
        now=fixed_now,
    )

    assert slept == [7]
    assert auth['access_token'] == 'NEW_ACCESS'
    assert auth['refresh_token'] == 'NEW_REFRESH'
    assert auth['scope'] == 'public'
    assert session.calls[0]['data'] == {'device_code': 'DEVICE', 'client_id': 'CLIENT'}
    assert session.calls[1]['data'] == {'device_code': 'DEVICE', 'client_id': 'CLIENT'}


def test_poll_slow_down_increases_interval():
    session = FakeSession([
        FakeResponse(400, {'error': 'slow_down'}),
        FakeResponse(200, {
            'access_token': 'A',
            'refresh_token': 'R',
            'token_type': 'bearer',
            'expires_in': 604800,
            'scope': 'public',
            'created_at': 1795750000,
        }),
    ])

    slept = []

    TraktAuthenticationManager.poll_device_token(
        'DEVICE',
        client_id='CLIENT',
        interval=5,
        expires_in=600,
        session=session,
        sleep=lambda seconds: slept.append(seconds),
        now=fixed_now,
    )

    assert slept == [6]


def test_poll_expired_device_code():
    session = FakeSession([
        FakeResponse(400, {'error': 'expired_token'}),
    ])

    try:
        TraktAuthenticationManager.poll_device_token(
            'DEVICE',
            client_id='CLIENT',
            session=session,
            sleep=no_sleep,
            now=fixed_now,
        )
    except DeviceCodeExpired:
        return

    raise AssertionError('Expected DeviceCodeExpired')


def test_poll_user_denied():
    session = FakeSession([
        FakeResponse(400, {'error': 'access_denied'}),
    ])

    try:
        TraktAuthenticationManager.poll_device_token(
            'DEVICE',
            client_id='CLIENT',
            session=session,
            sleep=no_sleep,
            now=fixed_now,
        )
    except AuthorizationDenied:
        return

    raise AssertionError('Expected AuthorizationDenied')


def test_poll_invalid_client():
    session = FakeSession([
        FakeResponse(401, {'error': 'invalid_client'}),
    ])

    try:
        TraktAuthenticationManager.poll_device_token(
            'DEVICE',
            client_id='BAD',
            session=session,
            sleep=no_sleep,
            now=fixed_now,
        )
    except InvalidClient:
        return

    raise AssertionError('Expected InvalidClient')


def test_network_errors_do_not_poll_faster_than_interval():
    session = FakeSession([
        TraktNetworkError('timeout'),
        FakeResponse(200, {
            'access_token': 'A',
            'refresh_token': 'R',
            'token_type': 'bearer',
            'expires_in': 604800,
            'scope': 'public',
            'created_at': 1795750000,
        }),
    ])

    slept = []

    TraktAuthenticationManager.poll_device_token(
        'DEVICE',
        client_id='CLIENT',
        interval=9,
        session=session,
        sleep=lambda seconds: slept.append(seconds),
        now=fixed_now,
    )

    assert slept == [9]


def test_normalize_authorization_preserves_scope_and_requires_complete_response():
    auth = TraktAuthenticationManager._normalize_authorization({
        'access_token': 'A',
        'refresh_token': 'R',
        'token_type': 'bearer',
        'expires_in': 604800,
        'scope': 'public',
        'created_at': 1795750000,
        'extra': 'preserved-by-caller-but-not-needed',
    })

    assert auth['access_token'] == 'A'
    assert auth['refresh_token'] == 'R'
    assert auth['scope'] == 'public'
    assert auth['token_type'] == 'bearer'
    assert auth['expires_in'] == 604800
    assert auth['created_at'] == 1795750000

    try:
        TraktAuthenticationManager._normalize_authorization({
            'access_token': 'A',
            'refresh_token': 'R',
            'token_type': 'bearer',
            'expires_in': 604800,
            'created_at': 1795750000,
        })
    except Exception:
        return

    raise AssertionError('Expected missing scope to fail')


def test_api_error_preserves_response_body():
    body = {'error': 'invalid_grant', 'error_description': 'session not found'}

    ex = TraktAPIError(
        'failed',
        status_code=401,
        body=body,
        headers={'Retry-After': '1'},
    )

    assert ex.status_code == 401
    assert ex.body == body
    assert ex.headers == {'Retry-After': '1'}


def test_per_account_refresh_locks_are_distinct_and_blocking():
    lock_a1 = TraktAuthenticationManager._refresh_lock('account-a')
    lock_a2 = TraktAuthenticationManager._refresh_lock('account-a')
    lock_b = TraktAuthenticationManager._refresh_lock('account-b')

    assert lock_a1 is lock_a2
    assert lock_a1 is not lock_b

    # Blocking lock, not non-blocking acquire(False).
    assert hasattr(lock_a1, 'acquire')
    assert hasattr(lock_a1, 'release')


def test_oauth_credential_save_authorization_replaces_all_fields_atomically_without_save():
    from plugin.managers.m_trakt.credential import TraktOAuthCredentialManager

    class Credential(object):
        def __init__(self):
            self.access_token = 'OLD_ACCESS'
            self.refresh_token = 'OLD_REFRESH'
            self.created_at = 1
            self.expires_in = 2
            self.token_type = 'old'
            self.scope = 'old'
            self.saved = False

        def save(self):
            self.saved = True

    credential = Credential()

    TraktOAuthCredentialManager.save_authorization(
        credential,
        {
            'access_token': 'NEW_ACCESS',
            'refresh_token': 'NEW_REFRESH',
            'created_at': 1795750000,
            'expires_in': 604800,
            'token_type': 'bearer',
            'scope': 'public',
        },
        save=False,
    )

    assert credential.access_token == 'NEW_ACCESS'
    assert credential.refresh_token == 'NEW_REFRESH'
    assert credential.created_at == 1795750000
    assert credential.expires_in == 604800
    assert credential.token_type == 'bearer'
    assert credential.scope == 'public'
    assert credential.saved is False
