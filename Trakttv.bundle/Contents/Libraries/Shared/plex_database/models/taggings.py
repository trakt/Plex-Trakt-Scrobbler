from plex_database.core import db

from peewee import *
from plex_database.models import MetadataItem
from plex_database.models import Tags


class Taggings(Model):
    class Meta:
        database = db
        db_table = 'taggings'

    metadata_item = ForeignKeyField(MetadataItem, null=True, related_name='taggings')
    tag = ForeignKeyField(Tags, null=True, related_name='taggings')

