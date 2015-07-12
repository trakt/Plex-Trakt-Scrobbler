from plugin.api.core.base import Service, expose
from plugin.managers import UserManager


class User(Service):
    __key__ = 'session.user'

    @expose
    def list(self, full=False):
        return [
            user.to_json(full=full)
            for user in UserManager.get.all()
        ]
