from plugin.models import Account
from plugin.models.core import db

from peewee import *


class ClientRule(Model):
    class Meta:
        database = db

    account = ForeignKeyField(Account, 'client_rules')

    machine_identifier = CharField(null=True)
    name = CharField(null=True)

    address = CharField(null=True)
