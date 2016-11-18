from plugin.models.core import db
from plugin.models.message import Message

from exception_wrappers.libraries.playhouse.apsw_ext import *


class Exception(Model):
    class Meta:
        database = db
        db_table = 'exception'

    error = ForeignKeyField(Message, 'exceptions', null=True)

    type = TextField()
    message = TextField()
    traceback = TextField()

    hash = CharField(null=True, max_length=32)

    timestamp = DateTimeField()
    version_base = CharField(max_length=12)
    version_branch = CharField(max_length=42)
