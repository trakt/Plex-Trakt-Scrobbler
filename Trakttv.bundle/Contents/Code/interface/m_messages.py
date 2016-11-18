from core.helpers import catch_errors, pad_title, try_convert, redirect

from plugin.core.constants import PLUGIN_PREFIX
from plugin.core.environment import translate as _
from plugin.core.message import InterfaceMessages
from plugin.managers.exception import ExceptionManager, MessageManager, VERSION_BASE
from plugin.models import Exception, Message

from ago import human
from datetime import datetime, timedelta
import logging

log = logging.getLogger(__name__)

ERROR_TYPES = [
    Message.Type.Exception,

    Message.Type.Warning,
    Message.Type.Error,
    Message.Type.Critical
]


@route(PLUGIN_PREFIX + '/messages/list')
@catch_errors
def ListMessages(days=14, version='latest', viewed=False, *args, **kwargs):
    # Cast `viewed` to boolean
    if type(viewed) is str:
        if viewed == 'None':
            viewed = None
        else:
            viewed = viewed == 'True'

    # Retrieve messages
    messages = list(List(
        days=try_convert(days, int),
        version=version,
        viewed=viewed
    ).order_by(
        Message.last_logged_at.desc()
    ).limit(50))

    total_messages = List(
        days=try_convert(days, int),
        version=version,
    ).count()

    # Construct container
    oc = ObjectContainer(
        title2=_("Messages")
    )

    # Add "Dismiss All" button
    if viewed is False and len(messages) > 1:
        oc.add(DirectoryObject(
            key=Callback(DismissMessages),
            title=pad_title(_("Dismiss all"))
        ))

    # Add interface messages
    for record in InterfaceMessages.records:
        # Pick object thumb
        if record.level >= logging.WARNING:
            thumb = R("icon-error.png")
        else:
            thumb = R("icon-notification.png")

        # Add object
        oc.add(DirectoryObject(
            key=PLUGIN_PREFIX + '/messages/list',
            title=pad_title('[%s] %s' % (logging.getLevelName(record.level).capitalize(), record.message)),
            thumb=thumb
        ))

    # Add stored messages
    for m in messages:
        if m.type is None or\
           m.summary is None:
            continue

        # Pick thumb
        if m.type == Message.Type.Exception:
            thumb = R("icon-exception-viewed.png") if m.viewed else R("icon-exception.png")
        elif m.type == Message.Type.Info:
            thumb = R("icon-notification-viewed.png") if m.viewed else R("icon-notification.png")
        else:
            thumb = R("icon-error-viewed.png") if m.viewed else R("icon-error.png")

        # Add object
        oc.add(DirectoryObject(
            key=Callback(ViewMessage, error_id=m.id),
            title=pad_title('[%s] %s' % (Message.Type.title(m.type), m.summary)),
            thumb=thumb
        ))

    # Append "View All" button
    if len(messages) != 50 and len(messages) < total_messages:
        oc.add(DirectoryObject(
            key=Callback(ListMessages, days=None, viewed=None),
            title=pad_title(_("View All"))
        ))

    return oc

@route(PLUGIN_PREFIX + '/messages/view')
@catch_errors
def ViewMessage(error_id, *args, **kwargs):
    # Retrieve message from database
    message = MessageManager.get.by_id(error_id)

    # Update `last_viewed_at` field
    message.last_viewed_at = datetime.utcnow()
    message.save()

    # Parse request headers
    web_client = Request.Headers.get('X-Plex-Product', '').lower() == 'plex web'

    # Build objects
    oc = ObjectContainer(
        title2='[%s] %s' % (Message.Type.title(message.type), Trim(message.summary))
    )

    if message.type == Message.Type.Exception:
        # Display exception samples
        for e in message.exceptions.order_by(Exception.timestamp.desc()).limit(50):
            since = datetime.utcnow() - e.timestamp

            callback = Callback(ViewMessage, error_id=error_id)

            if web_client:
                # Display exception traceback in Plex/Web
                callback = Callback(ViewException, exception_id=e.id)

            oc.add(DirectoryObject(
                key=callback,
                title=pad_title('[%s] %s: %s' % (human(since, precision=1), e.type, e.message)),
                thumb=R("icon-exception.png")
            ))
    elif message.type in [Message.Type.Info, Message.Type.Warning, Message.Type.Error, Message.Type.Critical]:
        # Display message code
        oc.add(DirectoryObject(
            key='',
            title=pad_title(_('Code: %s') % hex(message.code))
        ))

        # Display message description
        if message.description:
            oc.add(DirectoryObject(
                key='',
                title=pad_title(_('Description: %s') % message.description)
            ))

    return oc

@route(PLUGIN_PREFIX + '/exceptions/view')
@catch_errors
def ViewException(exception_id, *args, **kwargs):
    # Retrieve exception from database
    exception = ExceptionManager.get.by_id(exception_id)

    # Split traceback into lines
    traceback = exception.traceback

    if traceback:
        traceback = traceback.split('\n')

    # Build exception view
    oc = ObjectContainer(
        title2='%s: %s' % (exception.type, Trim(exception.message))
    )

    if not traceback:
        return oc

    for line in traceback:
        if not line:
            continue

        oc.add(DirectoryObject(
            key=Callback(ViewException, exception_id=exception_id),
            title=pad_title(line)
        ))

    return oc


@route(PLUGIN_PREFIX + '/messages/dismissAll')
@catch_errors
def DismissMessages(days=14, version='latest', *args, **kwargs):
    # Retrieve messages that match the specified criteria
    messages = List(
        days=days,
        version=version,
        viewed=False
    )

    # Mark all messages as viewed
    for message in messages:
        # Update `last_viewed_at` field
        message.last_viewed_at = datetime.utcnow()
        message.save()

    # Redirect back to the messages view
    return redirect(
        '/messages/list',
        days=days,
        version=version
    )


def Status(viewed=None):
    """Get the number and type of messages logged in the last week"""
    messages = List(
        days=14,
        version='latest',
        viewed=viewed
    )

    count = 0
    type = 'notification'

    # Process stored messages
    for message in messages:
        if message.type in ERROR_TYPES:
            type = 'error'

        count += 1

    # Process interface messages
    for record in InterfaceMessages.records:
        if record.level >= logging.ERROR:
            type = 'error'

        count += 1

    return count, type


def List(days=None, version=None, viewed=None):
    """Get messages logged in the last week"""
    where = []

    # Days
    if days is not None:
        where.append(
            Message.last_logged_at > datetime.utcnow() - timedelta(days=days)
        )

    # Version
    if version == 'latest':
        where.append(
            Message.version_base == VERSION_BASE
        )
    elif version is not None:
        log.warn('Unknown version specified: %r', version)

    # Viewed state
    if viewed is True:
        where.append(
            ~(Message.last_viewed_at >> None),
            Message.last_viewed_at > Message.last_logged_at
        )
    elif viewed is False:
        where.append(
            (Message.last_viewed_at >> None) | (Message.last_viewed_at < Message.last_logged_at)
        )

    # Build query
    if where:
        return MessageManager.get.where(*where)

    return MessageManager.get.all()


def Trim(value, length=45):
    if value and len(value) > length:
        return value[:length - 3] + "..."

    return value
