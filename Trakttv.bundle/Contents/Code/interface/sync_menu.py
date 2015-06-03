from core.helpers import timestamp, pad_title, get_filter, normalize
from core.localization import localization
from core.logger import Logger

from plugin.core.constants import PLUGIN_PREFIX
from plugin.managers import AccountManager
from plugin.models import Account, SyncResult
from plugin.sync import Sync, SyncData, SyncMedia, SyncMode

from ago import human
from datetime import datetime
from plex import Plex

L, LF = localization('interface.sync_menu')

log = Logger('interface.sync_menu')


# NOTE: pad_title(...) is used as a "hack" to force the UI to use 'media-details-list'

@route(PLUGIN_PREFIX + '/sync/accounts')
def AccountsMenu(refresh=None):
    # TODO adding profile thumbnails (from trakt.tv or plex.tv?) would be a nice addition
    oc = ObjectContainer(title2=L('accounts:title'), no_cache=True)

    AccountsStatus(oc)

    for account in AccountManager.get.all():
        oc.add(DirectoryObject(
            key=Callback(ControlsMenu, account_id=account.id),
            title=account.name
        ))

    return oc


def AccountsStatus(oc):
    # TODO display statistics (progress, est. time remaining, etc..)
    task = Sync.current

    if not task:
        # No task running
        return

    account = task.account

    # Build task title
    if task.data == SyncData.All:
        # <mode>
        title = normalize(SyncMode.title(task.mode))
    else:
        # <mode> [<data>]
        title = '%s [%s]' % (
            normalize(SyncMode.title(task.mode)),
            normalize(SyncData.title(task.data))
        )

    # - Progress percentage
    percent = task.progress.percent

    if percent is not None:
        title += ' (%2d%%)' % percent

    # Build task summary
    summary = 'Working'

    # - Estimated seconds remaining
    remaining_seconds = task.progress.remaining_seconds

    if remaining_seconds is not None:
        summary += ', %.02f seconds remaining' % remaining_seconds

    # Create items
    oc.add(DirectoryObject(
        key=Callback(AccountsMenu, refresh=timestamp()),
        title=pad_title('%s (%s) - Status' % (title, account.name)),
        summary='%s (click to refresh)' % summary
    ))

    oc.add(DirectoryObject(
        key=Callback(Cancel, account_id=account.id),
        title=pad_title('%s (%s) - Cancel' % (title, account.name))
    ))


@route(PLUGIN_PREFIX + '/sync')
def ControlsMenu(account_id=1, refresh=None):
    account = AccountManager.get(Account.id == account_id)

    oc = ObjectContainer(title2=LF('controls:title', account.name), no_cache=True)

    ControlsStatus(oc, account)  # TODO this should be moved to the `AccountsMenu` if there is multiple accounts

    #
    # Full
    #

    oc.add(DirectoryObject(
        key=Callback(Synchronize, account_id=account.id),
        title=pad_title(SyncMode.title(SyncMode.Full)),
        summary=ModeStatus(account, SyncMode.Full),
        thumb=R("icon-sync.png")
    ))

    #
    # Pull
    #

    oc.add(DirectoryObject(
        key=Callback(Pull, account_id=account.id),
        title=pad_title('%s from trakt' % SyncMode.title(SyncMode.Pull)),
        summary=ModeStatus(account, SyncMode.Pull),
        thumb=R("icon-sync_down.png")
    ))

    oc.add(DirectoryObject(
        key=Callback(FastPull, account_id=account.id),
        title=pad_title('%s from trakt' % SyncMode.title(SyncMode.FastPull)),
        summary=ModeStatus(account, SyncMode.FastPull),
        thumb=R("icon-sync_down.png")
    ))

    #
    # Push
    #

    sections = Plex['library'].sections()
    section_keys = []

    f_allow, f_deny = get_filter('filter_sections')

    for section in sections.filter(['show', 'movie'], titles=f_allow):
        oc.add(DirectoryObject(
            key=Callback(Push, account_id=account.id, section=section.key),
            title=pad_title('%s "%s" to trakt' % (SyncMode.title(SyncMode.Push), section.title)),
            summary=ModeStatus(account, SyncMode.Push, section.key),
            thumb=R("icon-sync_up.png")
        ))
        section_keys.append(section.key)

    if len(section_keys) > 1:
        oc.add(DirectoryObject(
            key=Callback(Push, account_id=account.id),
            title=pad_title('%s all to trakt' % SyncMode.title(SyncMode.Push)),
            summary=ModeStatus(account, SyncMode.Push),
            thumb=R("icon-sync_up.png")
        ))

    return oc


def ControlsStatus(oc, account):
    # TODO display statistics (progress, est. time remaining, etc..)
    task = Sync.current

    if not task:
        # No task running
        return

    if task.account.id != account.id:
        # Current task does not match this account
        return

    # Build task title
    if task.data == SyncData.All:
        # <mode>
        title = normalize(SyncMode.title(task.mode))
    else:
        # <mode> [<data>]
        title = '%s [%s]' % (
            normalize(SyncMode.title(task.mode)),
            normalize(SyncData.title(task.data))
        )

    # - Progress percentage
    percent = task.progress.percent

    if percent is not None:
        title += ' (%2d%%)' % percent

    # Build task summary
    summary = 'Working'

    # - Estimated seconds remaining
    remaining_seconds = task.progress.remaining_seconds

    if remaining_seconds is not None:
        summary += ', %.02f seconds remaining' % remaining_seconds

    # Create items
    oc.add(DirectoryObject(
        key=Callback(ControlsMenu, account_id=account.id, refresh=timestamp()),
        title=pad_title('%s - Status' % title),
        summary='%s (click to refresh)' % summary
    ))

    oc.add(DirectoryObject(
        key=Callback(Cancel, account_id=account.id),
        title=pad_title('%s - Cancel' % title)
    ))


def ModeStatus(account, mode, section=None):
    status = SyncResult.get_latest(account, mode, section).first()

    if status is None or status.latest is None:
        return 'Not run yet.'

    # Build status details string
    fragments = []

    if status.latest.ended_at:
        since = datetime.utcnow() - status.latest.ended_at

        if since.seconds < 1:
            fragments.append('Last run just a moment ago')
        else:
            fragments.append('Last run %s' % human(since, precision=1))

        if status.latest.started_at:
            elapsed = status.latest.ended_at - status.latest.started_at

            if elapsed.seconds < 1:
                fragments.append('taking less than a second')
            else:
                fragments.append('taking %s' % human(
                    elapsed,
                    precision=1,
                    past_tense='%s'
                ))

    if status.latest.success:
        fragments.append('was successful')
    else:
        message = 'failed'

        # Resolve errors
        errors = list(status.latest.get_errors())

        if len(errors) > 1:
            # Multiple errors
            message += ' (%d errors, %s)' % (len(errors), errors[0].summary)
        elif len(errors) == 1:
            # Single error
            message += ' (%s)' % errors[0].summary

        fragments.append(message)

    if len(fragments):
        return ', '.join(fragments) + '.'

    return 'Not run yet.'


@route(PLUGIN_PREFIX + '/sync/synchronize')
def Synchronize(account_id=1):
    # TODO implement options to change `SyncData` option per `Account`
    Sync.start(int(account_id), SyncMode.Full, SyncData.All, SyncMedia.All)

    return Redirect((PLUGIN_PREFIX + '/sync?account_id=%s') % account_id)


@route(PLUGIN_PREFIX + '/sync/fast_pull')
def FastPull(account_id=1):
    # TODO implement options to change `SyncData` option per `Account`
    Sync.start(int(account_id), SyncMode.FastPull, SyncData.All, SyncMedia.All)

    return Redirect((PLUGIN_PREFIX + '/sync?account_id=%s') % account_id)


@route(PLUGIN_PREFIX + '/sync/push')
def Push(account_id=1, section=None):
    # TODO implement options to change `SyncData` option per `Account`
    Sync.start(int(account_id), SyncMode.Push, SyncData.All, SyncMedia.All, section=section)

    return Redirect((PLUGIN_PREFIX + '/sync?account_id=%s') % account_id)


@route(PLUGIN_PREFIX + '/sync/pull')
def Pull(account_id=1):
    # TODO implement options to change `SyncData` option per `Account`
    Sync.start(int(account_id), SyncMode.Pull, SyncData.All, SyncMedia.All)

    return Redirect((PLUGIN_PREFIX + '/sync?account_id=%s') % account_id)


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
