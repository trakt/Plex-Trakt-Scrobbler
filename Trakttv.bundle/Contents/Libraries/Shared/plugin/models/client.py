from plugin.models import Account
from plugin.models.core import db

from playhouse.apsw_ext import *


class Client(Model):
    class Meta:
        database = db

    account = ForeignKeyField(Account, 'clients', null=True)

    # Identification
    machine_identifier = CharField(unique=True)
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
