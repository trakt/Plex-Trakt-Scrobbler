from plugin.models import *


def migrate(migrator, database):
    #
    # plex
    #

    PlexAccount.create_table()

    PlexBasicCredential.create_table()

    #
    # sync
    #

    SyncStatus.create_table()

    SyncResult.create_table()
    SyncResultError.create_table()
    SyncResultException.create_table()

    #
    # trakt
    #

    TraktAccount.create_table()

    TraktBasicCredential.create_table()
    TraktOAuthCredential.create_table()

    #
    # main
    #

    Account.create_table()
    Exception.create_table()
    Message.create_table()
    Session.create_table()

    ActionHistory.create_table()
    ActionQueue.create_table()

    Client.create_table()
    ClientRule.create_table()

    User.create_table()
    UserRule.create_table()
