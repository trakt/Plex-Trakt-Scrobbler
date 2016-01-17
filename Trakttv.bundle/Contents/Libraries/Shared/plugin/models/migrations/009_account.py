from plugin.models.core import db

from playhouse.apsw_ext import *


def migrate(migrator, database):
    # Account
    migrator.add_column('plex.account', 'title', CharField(null=True))
