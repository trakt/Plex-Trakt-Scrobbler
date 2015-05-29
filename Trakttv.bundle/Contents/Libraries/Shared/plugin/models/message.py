from plugin.models.core import db

from playhouse.apsw_ext import *


class MessageType(object):
    Generic     = 0x00
    Exception   = 0x01

    # Basic messages
    Info        = 0x02
    Warning     = 0x04
    Error       = 0x08
    Critical    = 0x16

    # Services
    Trakt       = 0x32


class Message(Model):
    Type = MessageType

    class Meta:
        database = db
        db_table = 'message'

    code = IntegerField(primary_key=True)
    type = IntegerField()

    # User-friendly explanation
    summary = CharField(max_length=160)  # Short single-line summary
    description = TextField()  # Extra related details
