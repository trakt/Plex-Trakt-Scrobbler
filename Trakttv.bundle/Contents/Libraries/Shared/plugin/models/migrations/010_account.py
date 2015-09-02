from plugin.models.core import db

from playhouse.apsw_ext import *


def migrate(migrator, database):
    # Account
    migrator.add_column('account', 'refreshed_at', DateTimeField(null=True))
