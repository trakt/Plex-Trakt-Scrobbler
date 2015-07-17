from playhouse.apsw_ext import *


def migrate(migrator, database):
    # PlexAccount
    migrator.add_column('plex.account', 'refreshed_at', DateTimeField(null=True))
