from exception_wrappers.libraries.playhouse.apsw_ext import *


def migrate(migrator, database):
    # Account
    migrator.add_column('plex.account', 'title', CharField(null=True))

#
# Schema specification (for migration verification)
#

SPEC = {
    'plex.account': {
        'id':                       'INTEGER PRIMARY KEY NOT NULL',
        'account_id':               'INTEGER NOT NULL',

        'key':                      'INTEGER',
        'username':                 'VARCHAR(255)',

        'title':                    'VARCHAR(255)',
        'thumb':                    'TEXT',

        'refreshed_at':             'DATETIME'
    }
}
