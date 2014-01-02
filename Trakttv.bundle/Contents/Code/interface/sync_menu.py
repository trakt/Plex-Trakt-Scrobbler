from core.helpers import SyncDownString, SyncUpString, itersections, timestamp
from plex.media_server import PMS
from sync.manager import SyncManager


@route('/applications/trakttv/sync')
def SyncMenu(refresh=None):
    if Prefs['username'] is None:
        return MessageContainer("Error", "No login information entered.")

    oc = ObjectContainer(title2=L("Sync"), no_history=True, no_cache=True)
    all_keys = []

    # Display details of current sync process
    task, handler = SyncManager.get_current()

    if task:
        progress = task.status.progress
        if progress:
            progress = ('%d%%' % (progress * 100))

        time_rem = task.status.seconds_remaining
        if time_rem:
            time_rem = int(round(time_rem, 0))

        oc.add(DirectoryObject(
            key=Callback(SyncMenu, refresh=timestamp()),
            title=('%s - Status' % handler.title) + ((' (%s)' % progress) if progress else ''),
            summary='Progress: %s, Estimated time remaining: %s (click to refresh)' % (
                progress or '?',
                '~%s seconds' % (time_rem or '?')
            )
        ))

        oc.add(DirectoryObject(
            key=Callback(Cancel),
            title='%s - Cancel' % handler.title
        ))

    oc.add(DirectoryObject(
        key=Callback(Synchronize),
        title='Synchronize',
        summary='Synchronize your ' + SyncDownString() + ' items with trakt.',
        thumb=R("icon-sync.png")
    ))

    for _, key, title in itersections(PMS.get_sections()):
        oc.add(DirectoryObject(
            key=Callback(Push, sections=[key]),
            title='Push "' + title + '" to trakt',
            summary='Push your ' + SyncUpString() + ' in the "' + title + '" section to trakt.',
            thumb=R("icon-sync_up.png")
        ))
        all_keys.append(key)

    if len(all_keys) > 1:
        oc.add(DirectoryObject(
            key=Callback(Push, sections=",".join(all_keys)),
            title='Push all to trakt',
            summary='Push your ' + SyncUpString() + ' items in all sections to trakt.',
            thumb=R("icon-sync_up.png")
        ))

    oc.add(DirectoryObject(
        key=Callback(Pull),
        title='Pull from trakt',
        summary='Pull your ' + SyncDownString() + ' items from trakt.',
        thumb=R("icon-sync_down.png")
    ))

    return oc


@route('/applications/trakttv/sync/synchronize')
def Synchronize():
    if not SyncManager.trigger_synchronize():
        return MessageContainer('Unable to sync', 'Syncing task already running, unable to start')

    return MessageContainer('Syncing started', 'Synchronize has started and will continue in the background')



@route('/applications/trakttv/sync/push')
def Push(sections):
    if not SyncManager.trigger_push():
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
