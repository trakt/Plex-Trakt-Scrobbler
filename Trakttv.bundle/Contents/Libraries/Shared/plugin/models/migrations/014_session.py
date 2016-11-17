from exception_wrappers.libraries.playhouse.apsw_ext import *


def migrate(migrator, database):
    # Session
    migrator.add_column('session', 'part', IntegerField(default=1))
    migrator.add_column('session', 'part_count', IntegerField(default=1))
    migrator.add_column('session', 'part_duration', IntegerField(null=True))

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

        'part':                     'INTEGER NOT NULL',
        'part_count':               'INTEGER NOT NULL',
        'part_duration':            'INTEGER',

        'duration':                 'INTEGER',
        'view_offset':              'INTEGER',
        'progress':                 'REAL',

        'updated_at':               'DATETIME'
    }
}
