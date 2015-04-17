from plugin.api.core.base import Service, expose
from plugin.managers import AccountManager


class Account(Service):
    __key__ = 'account'

    @expose
    def list(self, full=False):
        return [
            account.to_json(full=full)
            for account in AccountManager.get.all()
        ]

    @expose
    def get(self, full=False, **kwargs):
        query = dict([
            (key, value)
            for (key, value) in kwargs.items()
            if key in ['id', 'username']
        ])

        if len(query) < 1:
            return None

        return AccountManager.get(**query).to_json(full=full)
