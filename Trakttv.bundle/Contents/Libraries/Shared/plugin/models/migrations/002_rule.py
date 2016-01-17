from playhouse.apsw_ext import *


def migrate(migrator, database):
    # ClientRule
    migrator.drop_not_null('session.client.rule', 'account_id')
    migrator.add_column('session.client.rule', 'account_function', CharField(null=True))

    # UserRule
    migrator.drop_not_null('session.user.rule', 'account_id')
    migrator.add_column('session.user.rule', 'account_function', CharField(null=True))
