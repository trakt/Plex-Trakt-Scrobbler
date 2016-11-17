from exception_wrappers.libraries.playhouse.apsw_ext import *


def migrate(migrator, database):
    # Account
    migrator.add_column('account', 'refreshed_at', DateTimeField(null=True))

#
# Schema specification (for migration verification)
#

SPEC = {
    'account': {
        'id':                       'INTEGER PRIMARY KEY NOT NULL',

        'name':                     'VARCHAR(255)',
        'thumb':                    'TEXT',

        'refreshed_at':             'DATETIME'
    },
}
