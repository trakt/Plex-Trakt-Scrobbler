# ------------------------------------------------
# IMPORTANT
# These modules need to be loaded here first
# ------------------------------------------------
import core
import data
import plex
import pts
import sync
import interface
# ------------------------------------------------


from core.eventing import EventManager
from core.header import Header
from core.logger import Logger
from core.plugin import ART, NAME, ICON
from core.trakt import Trakt
from core.update_checker import UpdateChecker
from interface.main_menu import MainMenu
from plex.media_server import PMS
from pts.activity import Activity
from pts.scrobbler import Scrobbler
from pts.session_manager import SessionManager
from sync.legacy import SyncTrakt, CollectionSync
from sync.manager import SyncManager
from datetime import datetime


log = Logger('Code')


class Main:
    def __init__(self):
        # Check for updates first (required for use in header)
        self.update_checker = UpdateChecker()

        Header.show(self)

        if 'nowPlaying' in Dict and type(Dict['nowPlaying']) is dict:
            self.cleanup()
            Dict.Save()
        else:
            Dict['nowPlaying'] = dict()

        Main.update_config()

        self.session_manager = SessionManager()
        SyncManager.construct()

        EventManager.subscribe('notifications.timeline.created', self.timeline_created)

    @staticmethod
    def update_config():
        if Prefs['start_scrobble'] and Prefs['username'] is not None:
            Log('Autostart scrobbling')
            Dict["scrobble"] = True
        else:
            Dict["scrobble"] = False

        if Prefs['new_sync_collection'] and Prefs['username'] is not None:
            Log('Automatically sync new Items to Collection')
            Dict["new_sync_collection"] = True
        else:
            Dict["new_sync_collection"] = False

    def start(self):
        # Start syncing
        if Prefs['sync_startup'] and Prefs['username'] is not None:
            Log('Will autosync in 1 minute')
            Thread.CreateTimer(60, SyncTrakt)

        # Get current server version and save it to dict.
        server_version = PMS.get_server_version()
        if server_version:
            Log('Server Version is %s' % server_version)
            Dict['server_version'] = server_version

        # Check for updates
        self.update_checker.run_once(async=True)

        # Activity and Scrobbler
        Activity.start()
        Scrobbler.start()

        # Session Manager
        self.session_manager.start()

        # Sync manager
        SyncManager.start()

    def timeline_created(self, item):
        if not Dict['new_sync_collection']:
            return

        log.info("New File added to Libray: " + item['title'] + ' - ' + str(item['itemID']))

        # delay sync to wait for metadata
        Thread.CreateTimer(120, CollectionSync, True, item['itemID'], 'add')

    @staticmethod
    def cleanup():
        Log.Debug('Cleaning up stale or invalid sessions')

        for key, session in Dict['nowPlaying'].items():
            delete = False

            # Destroy invalid sessions
            if type(session) is not dict:
                delete = True
            elif 'update_required' not in session:
                delete = True
            elif 'last_updated' not in session:
                delete = True
            elif type(session['last_updated']) is not datetime:
                delete = True
            elif (datetime.now() - session['last_updated']).total_seconds() / 60 / 60 > 24:
                # Destroy sessions last updated over 24 hours ago
                Log.Debug('Session %s was last updated over 24 hours ago, queued for deletion', key)
                delete = True

            # Delete session or flag for update
            if delete:
                Log.Info('Session %s looks stale or invalid, deleting it now', key)
                del Dict['nowPlaying'][key]
            elif not session['update_required']:
                Log.Info('Queueing session %s for update', key)
                session['update_required'] = True

                # Update session in storage
                Dict['nowPlaying'][key] = session

        Log.Debug('Finished cleaning up')


def Start():
    ObjectContainer.art = R(ART)
    ObjectContainer.title1 = NAME
    DirectoryObject.thumb = R(ICON)
    DirectoryObject.art = R(ART)

    main = Main()
    main.start()


def ValidatePrefs():
    if Prefs['username'] is None:
        return MessageContainer("Error", "No login information entered.")

    if not Prefs['sync_watched'] and not Prefs['sync_ratings'] and not Prefs['sync_collection']:
        return MessageContainer("Error", "At least one sync type need to be enabled.")

    if not Prefs['start_scrobble']:
        Dict["scrobble"] = False

    status = Trakt.Account.test()

    if status['success']:
        Main.update_config()

        return MessageContainer(
            "Success",
            "Trakt responded with: %s " % status['message']
        )
    else:
        return MessageContainer(
            "Error",
            "Trakt responded with: %s " % status['message']
        )
