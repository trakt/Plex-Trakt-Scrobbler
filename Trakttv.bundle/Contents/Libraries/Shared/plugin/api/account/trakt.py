from plugin.api.core.base import Service, expose
from plugin.managers.m_trakt.account import TraktAccountManager


class TraktAccountService(Service):
    __key__ = 'account.trakt'

    @expose
    def delete(self, id):
        # Delete trakt account
        return TraktAccountManager.delete(
            id=id
        )
