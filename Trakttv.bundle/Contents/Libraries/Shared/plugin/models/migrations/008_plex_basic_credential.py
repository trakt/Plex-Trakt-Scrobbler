from exception_wrappers.libraries.playhouse.apsw_ext import *


def migrate(migrator, database):
    # PlexBasicCredential
    migrator.rename_column('plex.credential.basic', 'token', 'token_plex')
    migrator.add_column('plex.credential.basic', 'token_server', CharField(null=True))

#
# Schema specification (for migration verification)
#

SPEC = {
    'plex.credential.basic': {
        'id':                       'INTEGER PRIMARY KEY NOT NULL',
        'account_id':               'INTEGER NOT NULL',

        'password':                 'VARCHAR(255)',

        'token_plex':               'VARCHAR(255)',
        'token_server':             'VARCHAR(255)'
    },
}
