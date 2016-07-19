class Plugin(object):
    __key__ = None
    __priority__ = 0

    _client = None

    # TODO should this be changed to support both client and database updater plugins?
    def initialize(self, client):
        self._client = client

    @property
    def available(self):
        return True
