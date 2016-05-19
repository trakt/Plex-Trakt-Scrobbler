class Plugin(object):
    __key__ = None
    __priority__ = 0

    _client = None

    def initialize(self, client):
        self._client = client
