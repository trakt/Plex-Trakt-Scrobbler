from core.helpers import pad_title, timestamp

from plugin.core.constants import PLUGIN_PREFIX
from plugin.managers import ExceptionManager, MessageManager, VERSION_BASE, VERSION_BRANCH
from plugin.models import Exception, Message

from ago import human
from datetime import datetime, timedelta


@route(PLUGIN_PREFIX + '/messages/list')
def ListMessages():
    messages = List().order_by(Message.last_seen_at.desc()).limit(50)

    oc = ObjectContainer(
        title2="Messages"
    )

    for m in messages:
        if m.type is None or\
           m.summary is None or \
           m.description is None:
            continue

        callback = Callback(ListMessages)

        if m.type == Message.Type.Exception:
            callback = Callback(ViewMessage, error_id=m.id)

        oc.add(DirectoryObject(
            key=callback,
            title=pad_title('[%s] %s' % (Message.Type.title(m.type), m.summary))
        ))

    return oc

@route(PLUGIN_PREFIX + '/messages/view')
def ViewMessage(error_id):
    # Retrieve message from database
    message = MessageManager.get.by_id(error_id)

    # Parse request headers
    web_client = Request.Headers.get('X-Plex-Product', '').lower() == 'plex web'

    # Build objects
    oc = ObjectContainer(
        title2='[%s] %s' % (Message.Type.title(message.type), message.summary)
    )

    for e in message.exceptions.order_by(Exception.timestamp.desc()).limit(50):
        since = datetime.utcnow() - e.timestamp

        callback = Callback(ViewMessage, error_id=error_id)

        if web_client:
            # Display exception traceback in Plex/Web
            callback = Callback(ViewException, exception_id=e.id)

        oc.add(DirectoryObject(
            key=callback,
            title=pad_title('[%s] %s: %s' % (human(since, precision=1), e.type, e.message))
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
        title2='%s: %s' % (exception.type, exception.message)
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

def Count():
    """Get the number of messages logged in the last week"""
    return List().count()

def List():
    """Get messages logged in the last week"""
    since = datetime.utcnow() - timedelta(days=7)

    query = MessageManager.get.where(
        Message.last_seen_at > since,
        Message.version_base == VERSION_BASE,
        Message.version_branch == VERSION_BRANCH
    )

    return query
