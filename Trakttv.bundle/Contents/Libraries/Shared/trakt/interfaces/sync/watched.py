from trakt.interfaces.sync.base import SyncBaseInterface


class SyncWatchedInterface(SyncBaseInterface):
    path = 'sync/watched'
    flags = {'is_watched': True}

    def post(self, data):
        raise Exception("Invalid request")

    def delete(self, data):
        raise Exception("Invalid request")
