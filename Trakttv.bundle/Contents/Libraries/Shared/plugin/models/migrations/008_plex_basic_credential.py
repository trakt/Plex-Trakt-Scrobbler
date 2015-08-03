from plugin.models.core import db

from playhouse.apsw_ext import *


def migrate(migrator, database):
    # PlexBasicCredential
    migrator.rename_column('plex.credential.basic', 'token', 'token_plex')
    migrator.add_column('plex.credential.basic', 'token_server', CharField(null=True))
