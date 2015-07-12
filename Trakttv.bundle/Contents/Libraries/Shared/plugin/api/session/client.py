from plugin.api.core.base import Service, expose
from plugin.managers import ClientManager


class Client(Service):
    __key__ = 'session.client'

    @expose
    def list(self, full=False):
        return [
            client.to_json(full=full)
            for client in ClientManager.get.all()
        ]
