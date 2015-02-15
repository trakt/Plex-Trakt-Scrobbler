from plugin.models import *

from playhouse.apsw_ext import *


def migrate(migrator, database):
    Account.create_table()

    ActionHistory.create_table()
    ActionQueue.create_table()

    Session.create_table()

    Client.create_table()
    ClientRule.create_table()

    User.create_table()
    UserRule.create_table()
