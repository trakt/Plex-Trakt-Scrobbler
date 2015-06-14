from plugin.core.constants import PLUGIN_VERSION_BASE, PLUGIN_VERSION_BRANCH
from plugin.managers.core.base import Get, Manager
from plugin.models import Message

from datetime import datetime
import logging

VERSION_BASE = '.'.join([str(x) for x in PLUGIN_VERSION_BASE])
VERSION_BRANCH = PLUGIN_VERSION_BRANCH

log = logging.getLogger(__name__)


class GetMessage(Get):
    def from_exception(self, exception):
        # Find matching (or create new dummy) error message
        message = self.or_create(
            Message.type == Message.Type.Exception,
            Message.exception_hash == exception.hash,

            type=Message.Type.Exception,
            last_logged_at=datetime.utcnow(),

            exception_hash=exception.hash,
            revision=0,

            version_base=VERSION_BASE,
            version_branch=VERSION_BRANCH,

            summary=exception.message,
            description=exception.traceback
        )

        if message and not message._created:
            # Update `last_logged_at` timestamp
            message.last_logged_at = datetime.utcnow()
            message.save()

        return message


class MessageManager(Manager):
    get = GetMessage

    model = Message
