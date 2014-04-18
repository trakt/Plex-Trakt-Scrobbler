from trakt.interfaces.base import Interface, authenticated


class AccountInterface(Interface):
    path = 'account'

    @authenticated
    def test(self, credentials=None):
        """Test trakt credentials.

        This is useful for your configuration screen and is a simple way to test
        someone's trakt account.
        """
        response = self.request('test', credentials=credentials)

        data = self.get_data(response, catch_errors=False)

        if data is None:
            return None

        return data.get('status') == 'success'
