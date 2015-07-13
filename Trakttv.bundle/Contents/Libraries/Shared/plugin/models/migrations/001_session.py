from playhouse.apsw_ext import *


def migrate(migrator, database):
    migrator.add_column('session', 'updated_at', DateTimeField(null=True))
