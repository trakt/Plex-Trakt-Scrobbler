from exception_wrappers.libraries.playhouse.apsw_ext import *


def migrate(migrator, database):
    # ActionHistory
    migrator.add_column('action.history', 'rating_key', IntegerField(null=True))

    # ActionQueue
    migrator.add_column('action.queue', 'progress', FloatField(null=True))
    migrator.add_column('action.queue', 'rating_key', IntegerField(null=True))

#
# Schema specification (for migration verification)
#

SPEC = {
    'action.history': {
        'id':                       'INTEGER PRIMARY KEY NOT NULL',
        'account_id':               'INTEGER NOT NULL',
        'session_id':               'INTEGER',

        'rating_key':               'INTEGER',

        'event':                    'VARCHAR(255) NOT NULL',
        'performed':                'VARCHAR(255)',

        'queued_at':                'DATETIME NOT NULL',
        'sent_at':                  'DATETIME NOT NULL'
    },
    'action.queue': {
        'account_id':               'INTEGER NOT NULL',
        'session_id':               'INTEGER PRIMARY KEY',

        'progress':                 'REAL',
        'rating_key':               'INTEGER',

        'event':                    'VARCHAR(255) PRIMARY KEY NOT NULL',
        'request':                  'BLOB NOT NULL',

        'queued_at':                'DATETIME NOT NULL',
    },
}
