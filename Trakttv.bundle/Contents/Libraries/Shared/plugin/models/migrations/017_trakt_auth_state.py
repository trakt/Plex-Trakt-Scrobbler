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
        'auth_state': CharField(null=True),
    }
}
