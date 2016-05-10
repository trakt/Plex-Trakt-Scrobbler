from oem_framework.plugin import Plugin


class BaseStorage(Plugin):
    @property
    def client(self):
        return self._client

    @property
    def format(self):
        return self.provider.format

    @property
    def main(self):
        return self.provider.storage

    @property
    def provider(self):
        return self._client.provider
