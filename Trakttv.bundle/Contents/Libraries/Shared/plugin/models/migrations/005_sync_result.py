from plugin.models import SyncResult
from plugin.models.core import db

from playhouse.apsw_ext import *


def migrate(migrator, database):
    # SyncResult
    migrator.add_column('sync.result', 'trigger', IntegerField(default=SyncResult.Trigger.Manual))
