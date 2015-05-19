from plex_database.core import db

from peewee import *
from plex_database.models import LibrarySection


class SectionLocation(Model):
    class Meta:
        database = db
        db_table = 'section_locations'

    library_section = ForeignKeyField(LibrarySection, null=True, related_name='section_locations')

    root_path = CharField(null=True)
    available = BooleanField(default='t')

    scanned_at = DateTimeField(null=True)
    created_at = DateTimeField(null=True)
    updated_at = DateTimeField(null=True)
