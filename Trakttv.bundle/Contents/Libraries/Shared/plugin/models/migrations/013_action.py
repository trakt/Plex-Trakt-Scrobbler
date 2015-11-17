from plugin.models.core import db

from playhouse.apsw_ext import *


def migrate(migrator, database):
    # ActionHistory
    migrator.add_column('action.history', 'rating_key', IntegerField(null=True))

    # ActionQueue
    migrator.add_column('action.queue', 'progress', FloatField(null=True))
    migrator.add_column('action.queue', 'rating_key', IntegerField(null=True))
