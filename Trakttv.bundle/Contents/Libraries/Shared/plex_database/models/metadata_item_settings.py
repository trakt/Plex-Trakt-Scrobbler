from plex_database.core import db
from plex_database.models.account import Account

from peewee import *


class MetadataItemSettings(Model):
    class Meta:
        database = db
        db_table = 'metadata_item_settings'

    account = ForeignKeyField(Account, null=True, related_name='metadata_item_settings')

    guid = CharField(null=True)

    rating = FloatField(null=True)

    view_offset = IntegerField(null=True)
    view_count = IntegerField(null=True)
    last_viewed_at = DateTimeField(null=True)

    created_at = DateTimeField(null=True)
    updated_at = DateTimeField(null=True)

    skip_count = IntegerField(null=True, default=0)
    last_skipped_at = DateTimeField(null=True)

    changed_at = BigIntegerField(null=True, default=0)
