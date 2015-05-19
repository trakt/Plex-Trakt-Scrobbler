from plex_database.core import db
from plex_database.models.library_section import LibrarySection

from peewee import *


class MetadataItemType(object):
    Movie   = 1

    Show    = 2
    Season  = 3
    Episode = 4


class MetadataItem(Model):
    class Meta:
        database = db
        db_table = 'metadata_items'

    library_section = ForeignKeyField(LibrarySection, null=True, related_name='metadata_items')
    parent = ForeignKeyField('self', null=True, related_name='children')

    metadata_type = IntegerField(null=True)
    guid = CharField(null=True)
    media_item_count = IntegerField(null=True)

    title = CharField(null=True)
    title_sort = CharField(null=True)
    original_title = CharField(null=True)
    studio = CharField(null=True)

    rating = FloatField(null=True)
    rating_count = IntegerField(null=True)

    tagline = CharField(null=True)
    summary = TextField(null=True)
    trivia = TextField(null=True)
    quotes = TextField(null=True)

    content_rating = CharField(null=True)
    content_rating_age = IntegerField(null=True)

    index = IntegerField(null=True)
    absolute_index = IntegerField(null=True)

    duration = IntegerField(null=True)

    user_thumb_url = CharField(null=True)
    user_art_url = CharField(null=True)
    user_banner_url = CharField(null=True)
    user_music_url = CharField(null=True)
    user_fields = CharField(null=True)

    tags_genre = CharField(null=True)
    tags_collection = CharField(null=True)
    tags_director = CharField(null=True)
    tags_writer = CharField(null=True)
    tags_star = CharField(null=True)
    tags_country = CharField(null=True)

    originally_available_at = DateTimeField(null=True)
    available_at = DateTimeField(null=True)
    expires_at = DateTimeField(null=True)
    refreshed_at = DateTimeField(null=True)

    year = IntegerField(null=True)

    added_at = DateTimeField(null=True)
    created_at = DateTimeField(null=True)
    updated_at = DateTimeField(null=True)
    deleted_at = DateTimeField(null=True)

    extra_data = CharField(null=True)
    hash = CharField(null=True)

    audience_rating = FloatField(null=True)
    changed_at = BigIntegerField(default=0)
    resources_changed_at = BigIntegerField(default=0)

    @property
    def parent_id(self):
        return self._data['parent']
