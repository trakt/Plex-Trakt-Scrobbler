from plugin.models.core import db

from playhouse.apsw_ext import *


def migrate(migrator, database):
    # Message
    migrator.add_index('message', ('code', ), True)
