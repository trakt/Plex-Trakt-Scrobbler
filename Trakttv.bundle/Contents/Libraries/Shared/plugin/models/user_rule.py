from plugin.models import Account
from plugin.models.core import db

from peewee import *


class UserRule(Model):
    class Meta:
        database = db

    account = ForeignKeyField(Account, 'user_rules')

    name = CharField(null=True)
