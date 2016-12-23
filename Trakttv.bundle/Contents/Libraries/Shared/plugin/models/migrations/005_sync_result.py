from plugin.models import SyncResult

from exception_wrappers.libraries.playhouse.apsw_ext import *


def migrate(migrator, database):
    # SyncResult
    migrator.add_column('sync.result', 'trigger', IntegerField(default=SyncResult.Trigger.Manual))

#
# Schema specification (for migration verification)
#

SPEC = {
    'sync.result': {
        'id':                       'INTEGER PRIMARY KEY NOT NULL',
        'status_id':                'INTEGER NOT NULL',

        'trigger':                  'INTEGER NOT NULL',

        'started_at':               'DATETIME',
        'ended_at':                 'DATETIME',

        'success':                  'SMALLINT'
    }
}
