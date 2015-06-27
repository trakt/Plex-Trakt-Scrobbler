from plex_database.core import db
from plex_database.models.library_section import LibrarySection

from peewee import *


class Directory(Model):
    class Meta:
        database = db
        db_table = 'directories'

    library_section = ForeignKeyField(LibrarySection, null=True, related_name='directories')
    parent_directory = ForeignKeyField('self', null=True, related_name='children')

    path = CharField(null=True)

    created_at = DateTimeField(null=True)
    updated_at = DateTimeField(null=True)
    deleted_at = DateTimeField(null=True)
