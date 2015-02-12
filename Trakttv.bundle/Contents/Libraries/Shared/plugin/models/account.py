from plugin.models.core import db

from peewee import *


class Account(Model):
    class Meta:
        database = db

    username = CharField(primary_key=True)
    password = CharField()
