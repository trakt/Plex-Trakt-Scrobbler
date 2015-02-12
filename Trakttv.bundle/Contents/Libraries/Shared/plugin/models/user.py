from plugin.models.core import db

from peewee import *


class User(Model):
    class Meta:
        database = db

    id = IntegerField(unique=True)
    name = CharField(null=True)

    thumb = CharField(null=True)
