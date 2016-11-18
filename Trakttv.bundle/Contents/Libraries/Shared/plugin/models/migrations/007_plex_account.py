from exception_wrappers.libraries.playhouse.apsw_ext import *


def migrate(migrator, database):
    # PlexAccount
    migrator.add_column('plex.account', 'key', IntegerField(null=True, unique=True))

#
# Schema specification (for migration verification)
#

SPEC = {
    'plex.account': {
        'id':                       'INTEGER PRIMARY KEY NOT NULL',
        'account_id':               'INTEGER NOT NULL',

        'key':                      'INTEGER',
        'username':                 'VARCHAR(255)',

        'thumb':                    'TEXT',

        'refreshed_at':             'DATETIME'
    }
}
