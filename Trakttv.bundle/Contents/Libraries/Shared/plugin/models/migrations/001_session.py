from exception_wrappers.libraries.playhouse.apsw_ext import *


def migrate(migrator, database):
    migrator.add_column('session', 'updated_at', DateTimeField(null=True))

#
# Schema specification (for migration verification)
#

SPEC = {
    'session': {
        'id':                       'INTEGER PRIMARY KEY NOT NULL',
        'account_id':               'INTEGER',
        'client_id':                'VARCHAR(255)',
        'user_id':                  'INTEGER',

        'rating_key':               'INTEGER',
        'session_key':              'TEXT',

        'state':                    'VARCHAR(255)',

        'progress':                 'REAL',

        'duration':                 'INTEGER',
        'view_offset':              'INTEGER',

        'updated_at':               'DATETIME'
    }
}
