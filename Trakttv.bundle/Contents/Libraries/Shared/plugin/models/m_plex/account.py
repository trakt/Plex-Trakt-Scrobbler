from plugin.models.core import db
from plugin.models.account import Account

from playhouse.apsw_ext import *
import logging

log = logging.getLogger(__name__)


class PlexAccount(Model):
    class Meta:
        database = db
        db_table = 'plex.account'

    account = ForeignKeyField(Account, 'plex_accounts', unique=True)

    username = CharField(null=True, unique=True)

    def __init__(self, *args, **kwargs):
        super(PlexAccount, self).__init__(*args, **kwargs)

        self._basic_credential = None

    @property
    def basic(self):
        if self._basic_credential:
            return self._basic_credential

        return self.basic_credentials.first()

    @basic.setter
    def basic(self, value):
        self._basic_credential = value

    def to_json(self, full=False):
        result = {
            'id': self.id,
            'username': self.username
        }

        if not full:
            return result

        # Merge authorization details
        result['authorization'] = {
            'basic': {'valid': False}
        }

        # - Basic credentials
        basic = self.basic

        if basic is not None:
            result['authorization']['basic'] = basic.to_json(self)

        return result

    def __repr__(self):
        return '<PlexAccount username: %r>' % (
            self.username,
        )
