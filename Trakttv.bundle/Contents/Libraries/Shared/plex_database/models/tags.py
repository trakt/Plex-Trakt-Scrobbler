from plex_database.core import db

from peewee import *


class Tags(Model):
    class Meta:
        database = db
        db_table = 'tags'

    parent = ForeignKeyField('self', null=True, related_name='children')

    tag = CharField(null=True)
    tag_type = IntegerField(null=True)

    user_thumb_url = CharField(null=True)
    user_art_url = CharField(null=True)
    user_music_url = CharField(null=True)

    created_at = DateTimeField(null=True)
    updated_at = DateTimeField(null=True)

    tag_value = CharField(null=True)
    extra_data = CharField(null=True)

    key = CharField(null=True)

    @property
    def parent_id(self):
        return self._data['parent']
