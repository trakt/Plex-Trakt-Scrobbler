from plex_database.core import db

from peewee import *


class Tags(Model):
    class Meta:
        database = db
        db_table = 'tags'

    tag = CharField(null=True)
    tag_type = IntegerField(null=True)

