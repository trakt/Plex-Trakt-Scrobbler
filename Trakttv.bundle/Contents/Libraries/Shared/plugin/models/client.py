from plugin.models import Account
from plugin.models.core import db

from exception_wrappers.libraries.playhouse.apsw_ext import *


class Client(Model):
    class Meta:
        database = db
        db_table = 'session.client'

    account = ForeignKeyField(Account, 'clients', null=True)

    # Identification
    key = CharField(unique=True)
    name = CharField(null=True)

    # Device
    device_class = CharField(null=True)
    platform = CharField(null=True)
    product = CharField(null=True)
    version = CharField(null=True)

    # Network
    host = CharField(null=True)
    address = CharField(null=True)
    port = IntegerField(null=True)

    # Protocol
    protocol = CharField(null=True)
    protocol_capabilities = CharField(null=True)
    protocol_version = CharField(null=True)

    @property
    def account_id(self):
        return self._data.get('account')

    def to_json(self, full=False):
        result = {
            'id':       self.id,

            'key':      self.key,
            'name':     self.name,
            'address':  self.address,

            'platform': self.platform,
            'product':  self.product
        }

        if not full:
            return result

        # Select account
        account = self.account

        if account:
            result['account'] = account.to_json()

        return result

    def __repr__(self):
        return '<Client id: %r, key: %r>' % (self.id, self.key)
