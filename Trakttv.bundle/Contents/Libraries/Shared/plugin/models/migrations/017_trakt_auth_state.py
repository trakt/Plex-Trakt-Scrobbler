from exception_wrappers.libraries.playhouse.apsw_ext import *


def migrate(migrator, database):
    # TraktAccount
    # Add authentication state without touching existing account records,
    # Plex associations, OAuth credentials, watched history or sync preferences.
    migrator.add_column('trakt.account', 'auth_state', CharField(null=True))

#
# Schema specification (for migration verification)
#

SPEC = {
    'trakt.account': {
        'id':           'INTEGER PRIMARY KEY NOT NULL',
        'account_id':   'INTEGER NOT NULL',
        'username':     'VARCHAR(255)',
        'thumb':        'TEXT',
        'cover':        'TEXT',
        'timezone':    'TEXT',
        'refreshed_at': 'DATETIME',
        'auth_state':  'VARCHAR(255)',
    }
}
