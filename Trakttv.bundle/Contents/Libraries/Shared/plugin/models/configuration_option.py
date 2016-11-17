from plugin.models.core import db
from plugin.models.account import Account

from exception_wrappers.libraries.playhouse.apsw_ext import *


class ConfigurationOption(Model):
    class Meta:
        database = db
        db_table = 'configuration.option'

        primary_key = CompositeKey('account', 'key')

    account = ForeignKeyField(Account, 'sync_configuration')

    key = CharField(max_length=60)
    value = BlobField()
