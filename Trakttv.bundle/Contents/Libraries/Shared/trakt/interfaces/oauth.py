from trakt.core.helpers import deprecated
from trakt.helpers import build_url
from trakt.interfaces.base import Interface


class OAuthInterface(Interface):
    path = 'oauth'

    def authorize_url(self, redirect_uri, response_type='code', state=None, username=None):
        client_id = self.client.configuration['client.id']

        if not client_id:
            raise ValueError('"client.id" configuration parameter is required to generate the OAuth authorization url')

        return build_url(
            self.client.site_url,
            self.path, 'authorize',

            client_id=client_id,

            redirect_uri=redirect_uri,
            response_type=response_type,
            state=state,
            username=username
        )

    def pin_url(self):
        app_id = self.client.configuration['app.id']

        if not app_id:
            raise ValueError('"app.id" configuration parameter is required to generate the PIN authentication url')

        return build_url(
            self.client.site_url,
            'pin', app_id
        )

    @deprecated("Trakt['oauth'].token() method has been moved to Trakt['oauth'].token_exchange()")
    def token(self, code=None, redirect_uri=None, grant_type='authorization_code'):
        return self.token_exchange(code, redirect_uri, grant_type)

    def token_exchange(self, code=None, redirect_uri=None, grant_type='authorization_code'):
        client_id = self.client.configuration['client.id']
        client_secret = self.client.configuration['client.secret']

        if not client_id or not client_secret:
            raise ValueError('"client.id" and "client.secret" configuration parameters are required for token exchange')

        response = self.http.post(
            'token',
            data={
                'client_id': client_id,
                'client_secret': client_secret,

                'code': code,
                'redirect_uri': redirect_uri,
                'grant_type': grant_type
            },
            authenticated=False
        )

        data = self.get_data(response)

        if not data:
            return None

        return data

    def token_refresh(self, refresh_token=None, redirect_uri=None, grant_type='refresh_token'):
        client_id = self.client.configuration['client.id']
        client_secret = self.client.configuration['client.secret']

        if not client_id or not client_secret:
            raise ValueError('"client.id" and "client.secret" configuration parameters are required for token refresh')

        response = self.http.post(
            'token',
            data={
                'client_id': client_id,
                'client_secret': client_secret,

                'refresh_token': refresh_token,
                'redirect_uri': redirect_uri,
                'grant_type': grant_type
            },
            authenticated=False
        )

        data = self.get_data(response)

        if not data:
            return None

        return data
