from plex_database.core import db
from plex_database.models.directory import Directory
from plex_database.models.media_item import MediaItem

from peewee import *


class MediaPart(Model):
    class Meta:
        database = db
        db_table = 'media_parts'

    media_item = ForeignKeyField(MediaItem, null=True, related_name='media_parts')
    directory = ForeignKeyField(Directory, null=True, related_name='media_parts')

    hash  = CharField(null=True)
    open_subtitle_hash = CharField(null=True)

    file = CharField(null=True)
    index = IntegerField(null=True)

    size = BigIntegerField(null=True)
    duration = IntegerField(null=True)

    created_at = DateTimeField(null=True)
    updated_at = DateTimeField(null=True)
    deleted_at = DateTimeField(null=True)

    extra_data = CharField(null=True)
