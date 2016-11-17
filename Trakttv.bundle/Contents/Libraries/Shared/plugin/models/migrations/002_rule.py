from exception_wrappers.libraries.playhouse.apsw_ext import *


def migrate(migrator, database):
    # ClientRule
    migrator.drop_not_null('session.client.rule', 'account_id')
    migrator.add_column('session.client.rule', 'account_function', CharField(null=True))

    # UserRule
    migrator.drop_not_null('session.user.rule', 'account_id')
    migrator.add_column('session.user.rule', 'account_function', CharField(null=True))

#
# Schema specification (for migration verification)
#

SPEC = {
    'session.client.rule': {
        'id':                       'INTEGER PRIMARY KEY NOT NULL',
        'account_id':               'INTEGER',
        'account_function':         'VARCHAR(255)',

        'key':                      'VARCHAR(255)',
        'name':                     'VARCHAR(255)',
        'address':                  'VARCHAR(255)',

        'priority':                 'INTEGER NOT NULL'
    },
    'session.user.rule': {
        'id':                       'INTEGER PRIMARY KEY NOT NULL',
        'account_id':               'INTEGER',
        'account_function':         'VARCHAR(255)',

        'name':                     'VARCHAR(255)',

        'priority':                 'INTEGER NOT NULL'
    }
}
