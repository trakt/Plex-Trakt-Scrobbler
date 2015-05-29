from plugin.models.core import db
from plugin.models.message import Message

from playhouse.apsw_ext import *


class Exception(Model):
    class Meta:
        database = db
        db_table = 'exception'

    error = ForeignKeyField(Message, null=True)

    type = TextField()
    message = TextField()
    stack = TextField()
