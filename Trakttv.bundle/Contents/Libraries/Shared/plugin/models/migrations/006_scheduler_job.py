from plugin.models.core import db

from playhouse.apsw_ext import *


def migrate(migrator, database):
    migrator.drop_not_null('scheduler.job', 'trigger')
    migrator.drop_not_null('scheduler.job', 'due_at')
