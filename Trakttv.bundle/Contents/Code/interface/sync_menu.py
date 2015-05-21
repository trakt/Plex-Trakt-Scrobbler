from core.helpers import timestamp, pad_title, plural, get_filter, normalize
from core.localization import localization
from core.logger import Logger

from plugin.core.constants import PLUGIN_PREFIX
from plugin.managers import AccountManager
from plugin.models import Account
from plugin.sync import Sync, SyncData, SyncMedia, SyncMode

from ago import human
from datetime import datetime
from plex import Plex

L, LF = localization('interface.sync_menu')

log = Logger('interface.sync_menu')


# NOTE: pad_title(...) is used as a "hack" to force the UI to use 'media-details-list'

@route(PLUGIN_PREFIX + '/sync/accounts')
def AccountsMenu():
    # TODO adding profile thumbnails (from trakt.tv or plex.tv?) would be a nice addition
    oc = ObjectContainer(title2=L('accounts:title'), no_cache=True)

    for account in AccountManager.get.all():
        oc.add(DirectoryObject(
            key=Callback(ControlsMenu, account_id=account.id),
            title=account.name
        ))

    return oc

@route(PLUGIN_PREFIX + '/sync')
def ControlsMenu(account_id=1, refresh=None):
    account = AccountManager.get(Account.id == account_id)

    if account.id != 1:
        return MessageContainer('Not Implemented', "Multi-user syncing hasn't been implemented yet")

    oc = ObjectContainer(title2=LF('controls:title', account.name), no_cache=True)
    all_keys = []

    create_active_item(oc, account)  # TODO this should be moved to the `AccountsMenu` if there is multiple accounts

    oc.add(DirectoryObject(
        key=Callback(Synchronize, account_id=account.id),
        title=pad_title('Synchronize'),
        summary=get_task_status('synchronize'),
        thumb=R("icon-sync.png")
    ))

    f_allow, f_deny = get_filter('filter_sections')
    sections = Plex['library'].sections()

    for section in sections.filter(['show', 'movie'], titles=f_allow):
        oc.add(DirectoryObject(
            key=Callback(Push, account_id=account.id, section=section.key),
            title=pad_title('Push "%s" to trakt' % section.title),
            summary=get_task_status('push', section.key),
            thumb=R("icon-sync_up.png")
        ))
        all_keys.append(section.key)

    if len(all_keys) > 1:
        oc.add(DirectoryObject(
            key=Callback(Push, account_id=account.id),
            title=pad_title('Push all to trakt'),
            summary=get_task_status('push'),
            thumb=R("icon-sync_up.png")
        ))

    oc.add(DirectoryObject(
        key=Callback(Pull, account_id=account.id),
        title=pad_title('Pull from trakt'),
        summary=get_task_status('pull'),
        thumb=R("icon-sync_down.png")
    ))

    oc.add(DirectoryObject(
        key=Callback(FastPull, account_id=account.id),
        title=pad_title('Pull (Fast) from trakt'),
        summary=get_task_status('fast_pull'),
        thumb=R("icon-sync.png")
    ))

    return oc


def create_active_item(oc, account):
    # TODO implement active sync retrieval method
    return

    task, handler = SyncManager.get_current()
    if not task:
        return

    # Format values
    remaining = format_remaining(task.statistics.seconds_remaining)
    progress = format_percentage(task.statistics.progress)

    # Title
    title = '%s - Status' % normalize(handler.title)

    if progress:
        title += ' (%s)' % progress

    # Summary
    summary = task.statistics.message or 'Working'

    if remaining:
        summary += ', ~%s second%s remaining' % (remaining, plural(remaining))

    # Create items
    oc.add(DirectoryObject(
        key=Callback(ControlsMenu, account_id=account.id, refresh=timestamp()),
        title=pad_title(title),
        summary=summary + ' (click to refresh)'
    ))

    oc.add(DirectoryObject(
        key=Callback(Cancel, account_id=account.id),
        title=pad_title('%s - Cancel' % normalize(handler.title))
    ))


def format_percentage(value):
    if not value:
        return None

    return '%d%%' % (value * 100)

def format_remaining(value):
    if not value:
        return None

    return int(round(value, 0))


def get_task_status(key, section=None):
    # TODO implement task status retrieval method
    return '<Not Implemented>'

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
            result.append('taking %s' % human(
                status.previous_elapsed,
                precision=1,
                past_tense='%s'
            ))

    if status.previous_success is True:
        result.append('was successful')
    elif status.previous_timestamp:
        # Only add 'failed' fragment if there was actually a previous run
        message = 'failed'

        if status.error:
            message += ' (%s)' % status.error

        result.append(message)

    if len(result):
        return ', '.join(result) + '.'

    return 'Not run yet.'


@route(PLUGIN_PREFIX + '/sync/synchronize')
def Synchronize(account_id=1):
    # TODO implement options to change `SyncData` option per `Account`
    success, result = Sync.start(int(account_id), SyncMode.Full, SyncData.All, SyncMedia.All)

    # if not success:
    #     return MessageContainer(L('trigger_failure:title'), message)

    return MessageContainer(
        L('trigger_success:title'),
        LF('trigger_success:message', 'Synchronize')
    )


@route(PLUGIN_PREFIX + '/sync/fast_pull')
def FastPull(account_id=1):
    # TODO implement options to change `SyncData` option per `Account`
    success, result = Sync.start(int(account_id), SyncMode.FastPull, SyncData.All, SyncMedia.All)

    # if not success:
    #     return MessageContainer(L('trigger_failure:title'), message)

    return MessageContainer(
        L('trigger_success:title'),
        LF('trigger_success:message', 'Fast Pull')
    )


@route(PLUGIN_PREFIX + '/sync/push')
def Push(account_id=1, section=None):
    # TODO implement options to change `SyncData` option per `Account`
    success, result = Sync.start(int(account_id), SyncMode.Push, SyncData.All, SyncMedia.All, section=section)

    # if not success:
    #     return MessageContainer(L('trigger_failure:title'), message)

    return MessageContainer(
        L('trigger_success:title'),
        LF('trigger_success:message', 'Push')
    )


@route(PLUGIN_PREFIX + '/sync/pull')
def Pull(account_id=1):
    # TODO implement options to change `SyncData` option per `Account`
    success, result = Sync.start(int(account_id), SyncMode.Pull, SyncData.All, SyncMedia.All)

    # if not success:
    #     return MessageContainer(L('trigger_failure:title'), message)

    return MessageContainer(
        L('trigger_success:title'),
        LF('trigger_success:message', 'Pull')
    )


@route(PLUGIN_PREFIX + '/sync/cancel')
def Cancel():
    if not Sync.cancel():
        return MessageContainer(
            L('cancel_failure:title'),
            L('cancel_failure:message'),
        )

    return MessageContainer(
        L('cancel_success:title'),
        L('cancel_success:message')
    )
