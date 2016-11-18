from exception_wrappers.libraries.playhouse.apsw_ext import *


def migrate(migrator, database):
    # Account
    migrator.add_column('account', 'deleted', BooleanField(default=False))

#
# Schema specification (for migration verification)
#

SPEC = {
    'account': {
        'id':                       'INTEGER PRIMARY KEY NOT NULL',

        'name':                     'VARCHAR(255)',
        'thumb':                    'TEXT',

        'deleted':                  'SMALLINT NOT NULL',
        'refreshed_at':             'DATETIME'
    },
}
