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
from core.helpers import total_seconds, spawn
from core.plugin import ART, NAME, ICON
from core.trakt import Trakt
from core.update_checker import UpdateChecker
from interface.main_menu import MainMenu
from plex.plex_media_server import PlexMediaServer
from plex.plex_metadata import PlexMetadata
from pts.activity import Activity
from pts.scrobbler import Scrobbler
from pts.session_manager import SessionManager
from sync.manager import SyncManager
from datetime import datetime


log = Logger('Code')


MATCHER_MAP = {
    'Plex': 'plex',
    'Plex Extended': 'plex_extended'
}


class Main(object):
    modules = [
        # pts
        Activity,
        Scrobbler,

        # sync
        SyncManager,

        # plex
        PlexMetadata
    ]

    def __init__(self):
        self.update_checker = UpdateChecker()
        self.session_manager = SessionManager()

        Header.show(self)

        if 'nowPlaying' in Dict and type(Dict['nowPlaying']) is dict:
            self.cleanup()
            Dict.Save()
        else:
            Dict['nowPlaying'] = dict()

        Main.update_config()

        # Initialize modules
        for module in self.modules:
            if hasattr(module, 'initialize'):
                log.debug("Initializing module %s", module)
                module.initialize()

    @staticmethod
    def update_config(valid=None):
        preferences = Dict['preferences'] or {}

        # If no validation provided, use last stored result or assume true
        if valid is None:
            valid = preferences.get('valid', True)

        preferences['valid'] = valid

        preferences['scrobble'] = Prefs['start_scrobble'] and valid
        preferences['sync_run_library'] = Prefs['sync_run_library'] and valid

        preferences['matcher'] = MATCHER_MAP[Prefs['matcher']]

        # Ensure preferences dictionary is stored
        Dict['preferences'] = preferences
        Dict.Save()

        log.info('Preferences updated %s', preferences)
        EventManager.fire('preferences.updated', preferences)

    @classmethod
    def validate_auth(cls):
        if not Prefs['username'] or not Prefs['password']:
            log.warn('Authentication failed, username or password field empty')

            cls.update_config(False)
            return False

        status = Trakt.Account.test()

        if not status['success']:
            log.warn('Authentication failed, username or password is incorrect (trakt returned: %s)', status['message'])

            Main.update_config(False)
            return False

        log.info('Authentication successful')

        Main.update_config(True)
        return True

    def start(self):
        # Get current server version and save it to dict.
        server_version = PlexMediaServer.get_version()
        if server_version:
            Log('Server Version is %s' % server_version)
            Dict['server_version'] = server_version

        # Validate username/password
        spawn(self.validate_auth)

        # Check for updates
        self.update_checker.run_once(async=True)

        self.session_manager.start()

        # Start modules
        for module in self.modules:
            if hasattr(module, 'start'):
                log.debug("Starting module %s", module)
                module.start()

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
            elif total_seconds(datetime.now() - session['last_updated']) / 60 / 60 > 24:
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
    if not Prefs['sync_watched'] and not Prefs['sync_ratings'] and not Prefs['sync_collection']:
        Main.update_config(False)

        return MessageContainer(
            "Error",
            "At least one sync type need to be enabled."
        )

    if Main.validate_auth():
        return MessageContainer(
            "Success",
            "Authentication successful"
        )

    return MessageContainer(
        "Error",
        "Authentication failed, incorrect username or password"
    )
