from plugin.models.core import db
from plugin.models.account import Account
from plugin.models.scheduler_task import SchedulerTask

from croniter import croniter
from datetime import datetime
from playhouse.apsw_ext import *


class SchedulerJob(Model):
    class Meta:
        database = db
        db_table = 'scheduler.job'

        primary_key = CompositeKey('account', 'task')

    account = ForeignKeyField(Account, 'scheduler_jobs')
    task = ForeignKeyField(SchedulerTask, 'scheduler_jobs')

    trigger = TextField(null=True)

    ran_at = DateTimeField(null=True)
    due_at = DateTimeField(null=True)

    @property
    def next_at(self):
        if not self.trigger:
            return None

        cron = croniter(
            self.trigger,
            self.ran_at or datetime.utcnow()
        )

        # Calculate next due date
        return cron.get_next(datetime)
