from plex_database.core import db

from peewee import *
from plex_database.models import MetadataItem
from plex_database.models import Tags


class SectionLocation(Model):
    class Meta:
        database = db
        db_table = 'taggings'

    metadata_item = ForeignKeyField(MetadataItem, null=True, related_name='taggings')
    tag = ForeignKeyField(Tags, null=True, related_name='taggings')

    index = IntegerField(null=True)
    text = CharField(null=True)

    time_offset = BigIntegerField(null=True)
    end_time_offset = BigIntegerField(null=True)

    thumb_url = CharField(null=True)

    created_at = DateTimeField(null=True)
    extra_data = CharField(null=True)

