from core.helpers import pad_title, timestamp

from plugin.core.constants import PLUGIN_PREFIX
from plugin.core.environment import translate as _
from plugin.managers.exception import ExceptionManager, MessageManager, VERSION_BASE, VERSION_BRANCH
from plugin.models import Exception, Message

from ago import human
from datetime import datetime, timedelta

ERROR_TYPES = [
    Message.Type.Exception,

    Message.Type.Warning,
    Message.Type.Error,
    Message.Type.Critical
]


@route(PLUGIN_PREFIX + '/messages/list')
def ListMessages(viewed=None):
    # Cast `viewed` to boolean
    if type(viewed) is str:
        if viewed == 'None':
            viewed = None
        else:
            viewed = viewed == 'True'

    # Retrieve messages
    messages = list(List(
        viewed=viewed
    ).order_by(
        Message.last_logged_at.desc()
    ).limit(50))

    total_messages = List().count()

    # Construct container
    oc = ObjectContainer(
        title2=_("Messages")
    )

    for m in messages:
        if m.type is None or\
           m.summary is None:
            continue

        thumb = None

        if m.type == Message.Type.Exception:
            thumb = R("icon-exception-viewed.png") if m.viewed else R("icon-exception.png")
        elif m.type == Message.Type.Info:
            thumb = R("icon-notification-viewed.png") if m.viewed else R("icon-notification.png")
        elif m.type in ERROR_TYPES:
            thumb = R("icon-error-viewed.png") if m.viewed else R("icon-error.png")

        oc.add(DirectoryObject(
            key=Callback(ViewMessage, error_id=m.id),
            title=pad_title('[%s] %s' % (Message.Type.title(m.type), m.summary)),
            thumb=thumb
        ))

    # Append "View More" button
    if len(messages) != 50 and len(messages) < total_messages:
        oc.add(DirectoryObject(
            key=Callback(ListMessages),
            title=pad_title(_("View All"))
        ))

    return oc

@route(PLUGIN_PREFIX + '/messages/view')
def ViewMessage(error_id):
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
def ViewException(exception_id):
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

        length = len(line)

        line = line.lstrip()
        spaces = length - len(line)

        oc.add(DirectoryObject(
            key=Callback(ViewException, exception_id=exception_id),
            title=pad_title(('&nbsp;' * spaces) + line)
        ))

    return oc


def Status(viewed=None):
    """Get the number and type of messages logged in the last week"""
    messages = List(viewed=viewed)

    count = 0
    type = 'notification'

    for message in messages:
        if message.type in ERROR_TYPES:
            type = 'error'

        count += 1

    return count, type


def List(viewed=None):
    """Get messages logged in the last week"""
    since = datetime.utcnow() - timedelta(days=7)

    where = [
        Message.last_logged_at > since,
        Message.version_base == VERSION_BASE,
        Message.version_branch == VERSION_BRANCH
    ]

    if viewed is True:
        where.append(
            ~(Message.last_viewed_at >> None),
            Message.last_viewed_at > Message.last_logged_at
        )
    elif viewed is False:
        where.append(
            (Message.last_viewed_at >> None) | (Message.last_viewed_at < Message.last_logged_at)
        )

    return MessageManager.get.where(*where)


def Trim(value, length=45):
    if value and len(value) > length:
        return value[:length - 3] + "..."

    return value
