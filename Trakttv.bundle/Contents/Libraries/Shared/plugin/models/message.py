from plugin.core.environment import translate as _
from plugin.models.core import db

from exception_wrappers.libraries.playhouse.apsw_ext import *


class MessageCode(object):
    # Database (0x09)
    # - Schema (0x0901)
    DatabaseSchemaCorruptionReset = 0x90101

    # Release / Version (0x10)
    # - Upgrade (0x1001)
    UpgradePerformed = 0x100101
    # - Downgrade (0x1002)
    DowngradeUnclean = 0x100201

    # Network (0x11)
    # - Trakt (0x1101)
    TraktTimeout = 0x110101

    # TODO check for conflicting codes


class MessageType(object):
    __titles__  = None

    Generic     = 0x00
    Exception   = 0x01

    # Basic messages
    Info        = 0x02
    Warning     = 0x04
    Error       = 0x08
    Critical    = 0x16

    # Services
    Trakt       = 0x32
    Plex        = 0x64
    Sentry      = 0x128

    @classmethod
    def title(cls, value):
        if cls.__titles__ is None:
            cls.__titles__ = {
                MessageType.Generic:    None,
                MessageType.Exception:  _("Exception"),

                MessageType.Info:       _("Info"),
                MessageType.Warning:    _("Warning"),
                MessageType.Error:      _("Error"),
                MessageType.Critical:   _("Critical"),

                MessageType.Trakt:      _("Trakt.tv"),
                MessageType.Plex:       _("Plex.tv"),
                MessageType.Sentry:     _("Sentry")
            }

        return cls.__titles__.get(value)


class Message(Model):
    Code = MessageCode
    Type = MessageType

    class Meta:
        database = db
        db_table = 'message'

        indexes = (
            (('type', 'exception_hash'), True),
        )

    code = IntegerField(null=True)
    type = IntegerField()

    last_logged_at = DateTimeField()
    last_viewed_at = DateTimeField(null=True)

    # Tracking data
    exception_hash = CharField(null=True, max_length=32)
    revision = IntegerField(null=True)

    version_base = CharField(max_length=12)
    version_branch = CharField(max_length=42)

    # User-friendly explanation
    summary = CharField(null=True, max_length=160)  # Short single-line summary
    description = TextField(null=True)  # Extra related details

    @property
    def viewed(self):
        if not self.last_viewed_at:
            return False

        return self.last_viewed_at > self.last_logged_at
