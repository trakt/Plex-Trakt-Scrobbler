from plugin.models.core import db

from playhouse.apsw_ext import *


class Account(Model):
    class Meta:
        database = db

    username = CharField(unique=True)
    password = CharField()

    token = CharField(null=True)
