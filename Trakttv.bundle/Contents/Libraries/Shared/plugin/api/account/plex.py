from plugin.api.core.base import Service, expose
from plugin.managers.m_plex.account import PlexAccountManager


class PlexAccountService(Service):
    __key__ = 'account.plex'

    @expose
    def delete(self, id):
        # Delete plex account
        return PlexAccountManager.delete(
            id=id
        )
