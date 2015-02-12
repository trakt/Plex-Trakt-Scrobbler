from plugin.models.core import db

from peewee import *


class Client(Model):
    class Meta:
        database = db

    # Identification
    machine_identifier = CharField(unique=True)
    name = CharField(null=True)

    # Device
    device_class = CharField(null=True)
    platform = CharField(null=True)
    product = CharField(null=True)
    version = CharField(null=True)

    # Network
    host = CharField(null=True)
    address = CharField(null=True)
    port = IntegerField(null=True)

    # Protocol
    protocol = CharField(null=True)
    protocol_capabilities = CharField(null=True)
    protocol_version = CharField(null=True)
