from plugin.core.constants import PLUGIN_VERSION_BASE, PLUGIN_VERSION_BRANCH
from plugin.managers.core.base import Get, Manager
from plugin.models import Message

from datetime import datetime
import logging

VERSION_BASE = '.'.join([str(x) for x in PLUGIN_VERSION_BASE])
VERSION_BRANCH = PLUGIN_VERSION_BRANCH

log = logging.getLogger(__name__)


class GetMessage(Get):
    def _log(self, message_type, *args, **kwargs):
        # Find matching (or create new dummy) error message
        message = self.or_create(
            Message.type == message_type,
            *args,

            type=message_type,
            last_logged_at=datetime.utcnow(),

            revision=0,

            version_base=VERSION_BASE,
            version_branch=VERSION_BRANCH,
            **kwargs
        )

        if message and not message._created:
            # Update summary/description
            if kwargs.get('summary'):
                message.summary = kwargs['summary']

            if kwargs.get('description'):
                message.description = kwargs['description']

            # Update `last_logged_at` timestamp
            message.last_logged_at = datetime.utcnow()

            # Update version details
            message.version_base = VERSION_BASE
            message.version_branch = VERSION_BRANCH

            # Save changes to message
            message.save()

        return message

    def from_exception(self, exception, message_type=Message.Type.Exception):
        # Log exception
        return self._log(
            message_type,

            # Query
            Message.exception_hash == exception.hash,

            # Parameters
            exception_hash=exception.hash,

            summary=exception.message,
            description=exception.traceback
        )

    def from_message(self, level, message, code=None, description=None):
        # Convert `level` to `Message.Type`
        if level == logging.INFO:
            type = Message.Type.Info
        elif level == logging.WARNING:
            type = Message.Type.Warning
        elif level == logging.ERROR:
            type = Message.Type.Error
        elif level == logging.CRITICAL:
            type = Message.Type.Critical
        else:
            raise ValueError('Unknown value for "level" parameter')

        # Log message
        return self._log(
            type,

            # Query
            Message.code == code,

            # Parameters
            code=code,

            summary=message,
            description=description
        )


class MessageManager(Manager):
    get = GetMessage

    model = Message
