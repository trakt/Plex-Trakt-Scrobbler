from plugin.models.core import db

from exception_wrappers.libraries.playhouse.apsw_ext import *


def migrate(migrator, database):
    migrator.create_tables(
        SchedulerTask,
        SchedulerJob
    )


class Account(Model):
    class Meta:
        database = db

    name = CharField(null=True, unique=True)
    thumb = TextField(null=True)


class SchedulerTask(Model):
    class Meta:
        database = db
        db_table = 'scheduler.task'

    key = CharField(max_length=60, primary_key=True)


class SchedulerJob(Model):
    class Meta:
        database = db
        db_table = 'scheduler.job'

        primary_key = CompositeKey('account', 'task')

    account = ForeignKeyField(Account, 'scheduler_jobs')
    task = ForeignKeyField(SchedulerTask, 'scheduler_jobs')

    trigger = TextField()

    ran_at = DateTimeField(null=True)
    due_at = DateTimeField()

#
# Schema specification (for migration verification)
#

SPEC = {
    'scheduler.task': {
        'key':                      'VARCHAR(60) PRIMARY KEY NOT NULL'
    },
    'scheduler.job': {
        'account_id':               'INTEGER PRIMARY KEY NOT NULL',
        'task_id':                  'VARCHAR(60) PRIMARY KEY NOT NULL',

        'trigger':                  'TEXT NOT NULL',

        'ran_at':                   'DATETIME',
        'due_at':                   'DATETIME NOT NULL'
    }
}
