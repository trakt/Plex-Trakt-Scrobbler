from plugin.models.core import db

from playhouse.apsw_ext import *


def migrate(migrator, database):
    SchedulerTask.create_table()
    SchedulerJob.create_table()


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
