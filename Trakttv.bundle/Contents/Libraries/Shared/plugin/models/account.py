from plugin.models.core import db

from playhouse.apsw_ext import *
import logging

log = logging.getLogger(__name__)


class Account(Model):
    class Meta:
        database = db

    name = TextField(unique=True)

    def __init__(self, *args, **kwargs):
        super(Account, self).__init__(*args, **kwargs)

        self._plex_account = None
        self._trakt_account = None

    @property
    def plex(self):
        if self._plex_account:
            return self._plex_account

        return self.plex_accounts.first()

    @plex.setter
    def plex(self, value):
        self._plex_account = value

    @property
    def trakt(self):
        if self._trakt_account:
            return self._trakt_account

        return self.trakt_accounts.first()

    @trakt.setter
    def trakt(self, value):
        self._trakt_account = value

    def to_json(self, full=False):
        result = {
            'id': self.id,
            'name': self.name
        }

        if not full:
            return result

        # plex
        plex = self.plex

        if plex:
            result['plex'] = plex.to_json(full=full)

        # trakt
        trakt = self.trakt

        if trakt:
            result['trakt'] = trakt.to_json(full=full)

        return result

    def __repr__(self):
        return '<Account name: %r>' % (
            self.name
        )
