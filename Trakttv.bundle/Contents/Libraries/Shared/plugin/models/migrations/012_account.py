from plugin.models.core import db

from playhouse.apsw_ext import *


def migrate(migrator, database):
    # Account
    migrator.add_column('account', 'deleted', BooleanField(default=False))
