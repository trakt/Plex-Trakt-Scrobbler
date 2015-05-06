from plugin.models.core import db

from playhouse.apsw_ext import *
import logging

log = logging.getLogger(__name__)


class Account(Model):
    class Meta:
        database = db

    name = TextField(unique=True)

    @property
    def plex(self):
        return self.plex_accounts.first()

    @property
    def trakt(self):
        return self.trakt_accounts.first()

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
