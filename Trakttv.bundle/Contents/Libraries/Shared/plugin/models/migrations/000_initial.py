from plugin.models import *


def migrate(migrator, database):
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
    Session.create_table()

    ActionHistory.create_table()
    ActionQueue.create_table()

    Client.create_table()
    ClientRule.create_table()

    User.create_table()
    UserRule.create_table()
