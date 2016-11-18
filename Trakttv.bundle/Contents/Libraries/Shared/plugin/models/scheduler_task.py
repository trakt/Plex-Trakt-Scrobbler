from plugin.models.core import db

from exception_wrappers.libraries.playhouse.apsw_ext import *


class SchedulerTask(Model):
    class Meta:
        database = db
        db_table = 'scheduler.task'

    key = CharField(max_length=60, primary_key=True)
