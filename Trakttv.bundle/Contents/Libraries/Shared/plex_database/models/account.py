from plex_database.core import db

from peewee import *


class Account(Model):
    class Meta:
        database = db
        db_table = 'accounts'

    name = CharField(null=True)

    hashed_password = CharField(null=True)
    salt = CharField(null=True)

    created_at = DateTimeField(null=True)
    updated_at = DateTimeField(null=True)

    default_audio_language = CharField(null=True)
    default_subtitle_language = CharField(null=True)

    auto_select_subtitle = BooleanField(null=True)
    auto_select_audio = BooleanField(null=True)
