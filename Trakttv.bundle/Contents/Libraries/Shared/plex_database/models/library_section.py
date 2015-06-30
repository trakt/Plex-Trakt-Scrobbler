from plex_database.core import db

from peewee import *


class LibrarySectionType(object):
    Movie   = 1
    Show    = 2
    Music   = 8
    Photo   = 13


class LibrarySection(Model):
    class Meta:
        database = db
        db_table = 'library_sections'

    library_id = IntegerField(null=True)  # empty

    uuid = CharField(null=True)

    name = CharField(null=True)
    name_sort = CharField(null=True)

    section_type = IntegerField(null=True)

    language = CharField(null=True)
    agent = CharField(null=True)
    scanner = CharField(null=True)

    user_thumb_url = CharField(null=True)
    user_art_url = CharField(null=True)
    user_theme_music_url = CharField(null=True)

    public = BooleanField(null=True)

    created_at = DateTimeField(null=True)
    updated_at = DateTimeField(null=True)
    scanned_at = DateTimeField(null=True)
    changed_at = BigIntegerField(null=True)

    display_secondary_level = BooleanField(null=True)

    user_fields = CharField(null=True)

    query_xml = TextField(null=True)
    query_type = IntegerField(null=True)
