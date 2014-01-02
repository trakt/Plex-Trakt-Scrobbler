from core.helpers import SyncDownString, SyncUpString, finditems, iterget, extend, matches, all, itersections
from plex.media_server import PMS
from sync.manager import SyncManager


@route('/applications/trakttv/sync')
def SyncMenu():
    if Prefs['username'] is None:
        return MessageContainer("Error", "No login information entered.")

    oc = ObjectContainer(title2=L("Sync"), no_history=True, no_cache=True)
    all_keys = []

    oc.add(DirectoryObject(
        key=Callback(Synchronize),
        title='Synchronize items in ALL sections with trakt.',
        summary='Synchronize your ' + SyncDownString() + ' items with trakt.',
        thumb=R("icon-sync.png")
    ))

    for _, key, title in itersections(PMS.get_sections()):
        oc.add(DirectoryObject(
            key=Callback(Push, sections=[key]),
            title='Push items in "' + title + '" to trakt.',
            summary='Push your ' + SyncUpString() + ' in the "' + title + '" section to trakt.',
            thumb=R("icon-sync_up.png")
        ))
        all_keys.append(key)

    if len(all_keys) > 1:
        oc.add(DirectoryObject(
            key=Callback(Push, sections=",".join(all_keys)),
            title='Push items in ALL sections to trakt.',
            summary='Push your ' + SyncUpString() + ' items in all sections to trakt.',
            thumb=R("icon-sync_up.png")
        ))

    oc.add(DirectoryObject(
        key=Callback(Pull),
        title='Pull items from Trakt.tv',
        summary='Pull your ' + SyncDownString() + ' items from trakt.',
        thumb=R("icon-sync_down.png")
    ))

    return oc


@route('/applications/trakttv/sync/synchronize')
def Synchronize():
    if not SyncManager.trigger_synchronize():
        return MessageContainer('Unable to sync', 'Sync process already running, unable to start')

    return MessageContainer('Syncing started', 'Synchronize has started and will continue in the background')



@route('/applications/trakttv/sync/push')
def Push(sections):
    if not SyncManager.trigger_push():
        return MessageContainer('Unable to sync', 'Sync process already running, unable to start')

    return MessageContainer('Syncing started', 'Push has been triggered and will continue in the background')


@route('/applications/trakttv/sync/pull')
def Pull():
    if not SyncManager.trigger_pull():
        return MessageContainer('Unable to sync', 'Sync process already running, unable to start')

    return MessageContainer('Syncing started', 'Pull has been triggered and will continue in the background')
