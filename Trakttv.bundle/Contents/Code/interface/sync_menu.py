from core.helpers import timestamp, pad_title
from plex.plex_media_server import PlexMediaServer
from sync.manager import SyncManager
from datetime import datetime
from ago import human


# NOTE: pad_title(...) is used as a "hack" to force the UI to use 'media-details-list'

@route('/applications/trakttv/sync')
def SyncMenu(refresh=None):
    if Prefs['username'] is None:
        return MessageContainer("Error", "No login information entered.")

    oc = ObjectContainer(title2=L("Sync"), no_history=True, no_cache=True)
    all_keys = []

    # Display details of current sync process
    task, handler = SyncManager.get_current()

    if task:
        progress = task.statistics.progress
        if progress:
            progress = ('%d%%' % (progress * 100))

        time_rem = task.statistics.seconds_remaining
        if time_rem:
            time_rem = int(round(time_rem, 0))

        oc.add(DirectoryObject(
            key=Callback(SyncMenu, refresh=timestamp()),
            title=pad_title(('%s - Status' % handler.title) + ((' (%s)' % progress) if progress else '')),
            summary='Progress: %s, estimated time remaining: %s (click to refresh)' % (
                progress or '?',
                '~%s seconds' % (time_rem or '?')
            )
        ))

        oc.add(DirectoryObject(
            key=Callback(Cancel),
            title=pad_title('%s - Cancel' % handler.title)
        ))

    oc.add(DirectoryObject(
        key=Callback(Synchronize),
        title=pad_title('Synchronize'),
        summary=get_task_status('synchronize'),
        thumb=R("icon-sync.png")
    ))

    for _, key, title in PlexMediaServer.get_sections(['show', 'movie']):
        oc.add(DirectoryObject(
            key=Callback(Push, section=key),
            title=pad_title('Push "' + title + '" to trakt'),
            summary=get_task_status('push', key),
            thumb=R("icon-sync_up.png")
        ))
        all_keys.append(key)

    if len(all_keys) > 1:
        oc.add(DirectoryObject(
            key=Callback(Push),
            title=pad_title('Push all to trakt'),
            summary=get_task_status('push'),
            thumb=R("icon-sync_up.png")
        ))

    oc.add(DirectoryObject(
        key=Callback(Pull),
        title=pad_title('Pull from trakt'),
        summary=get_task_status('pull'),
        thumb=R("icon-sync_down.png")
    ))

    return oc


def get_task_status(key, section=None):
    result = []

    status = SyncManager.get_status(key, section)

    if status.previous_timestamp:
        since = datetime.utcnow() - status.previous_timestamp

        if since.seconds < 1:
            result.append('Last run just a moment ago')
        else:
            result.append('Last run %s' % human(since, precision=1))

    if status.previous_elapsed:
        if status.previous_elapsed.seconds < 1:
            result.append('taking less than a second')
        else:
            result.append('taking %s' % human(status.previous_elapsed, precision=1, past_tense='%s'))

    if status.previous_success is True:
        result.append('was successful')
    elif status.previous_timestamp:
        # Only add 'failed' fragment if there was actually a previous run
        result.append('failed')

    if len(result):
        return ', '.join(result) + '.'

    return 'Not run yet.'


@route('/applications/trakttv/sync/synchronize')
def Synchronize():
    if not SyncManager.trigger_synchronize():
        return MessageContainer('Unable to sync', 'Syncing task already running, unable to start')

    return MessageContainer('Syncing started', 'Synchronize has started and will continue in the background')



@route('/applications/trakttv/sync/push')
def Push(section=None):
    if not SyncManager.trigger_push(section):
        return MessageContainer('Unable to sync', 'Syncing task already running, unable to start')

    return MessageContainer('Syncing started', 'Push has been triggered and will continue in the background')


@route('/applications/trakttv/sync/pull')
def Pull():
    if not SyncManager.trigger_pull():
        return MessageContainer('Unable to sync', 'Syncing task already running, unable to start')

    return MessageContainer('Syncing started', 'Pull has been triggered and will continue in the background')


@route('/applications/trakttv/sync/cancel')
def Cancel():
    if not SyncManager.cancel():
        return MessageContainer('Unable to cancel', 'There is no syncing task running')

    return MessageContainer('Syncing cancelled', 'Syncing task has been notified to cancel')
