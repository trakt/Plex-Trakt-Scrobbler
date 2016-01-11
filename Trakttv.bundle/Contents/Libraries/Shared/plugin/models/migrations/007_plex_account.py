from plugin.models.core import db

from playhouse.apsw_ext import *


def migrate(migrator, database):
    # PlexAccount
    migrator.add_column('plex.account', 'key', IntegerField(null=True, unique=True))
