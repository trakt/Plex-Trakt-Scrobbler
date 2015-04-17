from plugin.models.core import db

from playhouse.apsw_ext import *
import logging

log = logging.getLogger(__name__)


class Account(Model):
    class Meta:
        database = db

    name = TextField(unique=True)

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

        trakt_account = self.trakt

        if trakt_account:
            result['trakt'] = trakt_account.to_json(full=full)

        return result

    def __repr__(self):
        return '<Account username: %r>' % (
            self.username,
        )
