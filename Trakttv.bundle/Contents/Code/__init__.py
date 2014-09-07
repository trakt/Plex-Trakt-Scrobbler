# ------------------------------------------------
# IMPORTANT
# These modules need to be loaded here first
# ------------------------------------------------
import core
import data
import pts
# TODO import sync
import interface
# ------------------------------------------------


from core.configuration import Configuration
from core.eventing import EventManager
from core.header import Header
from core.logger import Logger
from core.logging_handler import PlexHandler
from core.helpers import total_seconds, spawn, get_pref, schedule
from core.plugin import ART, NAME, ICON, PLUGIN_VERSION, PLUGIN_IDENTIFIER
from core.update_checker import UpdateChecker
from interface.main_menu import MainMenu
from pts.scrobbler import Scrobbler
# TODO from pts.session_manager import SessionManager
# TODO from sync.manager import SyncManager

from datetime import datetime
from plex import Plex
from plex_activity import Activity
from trakt import Trakt
import hashlib
import logging


log = Logger('Code')


class Main(object):
    modules = [
        # pts
        Activity,
        Scrobbler,

        # sync
        # TODO SyncManager,
    ]

    loggers_allowed = [
        'plex',
        'plex_activity',
        'plex_metadata',
        'pyemitter',
        'requests',
        'trakt'
    ]

    def __init__(self):
        self.update_checker = UpdateChecker()
        # TODO self.session_manager = SessionManager()

        Header.show(self)

        if 'nowPlaying' in Dict and type(Dict['nowPlaying']) is dict:
            self.cleanup()
            Dict.Save()
        else:
            Dict['nowPlaying'] = dict()

        Main.update_config()

        self.init_logging()
        self.init_trakt()

        # Initialize modules
        for module in self.modules:
            if hasattr(module, 'initialize'):
                log.debug("Initializing module %s", module)
                module.initialize()

    @classmethod
    def init_logging(cls):
        logging.basicConfig(level=logging.DEBUG)

        for name in cls.loggers_allowed:
            logger = logging.getLogger(name)

            logger.setLevel(logging.DEBUG)
            logger.handlers = [PlexHandler()]

    @staticmethod
    def init_trakt():
        def get_credentials():
            password_hash = hashlib.sha1(Prefs['password'])

            return (
                Prefs['username'],
                password_hash.hexdigest()
            )

        Trakt.configure(
            # Application
            api_key='ba5aa61249c02dc5406232da20f6e768f3c82b28',

            # Version
            plugin_version=PLUGIN_VERSION,
            media_center_version=Plex.version(),

            # Account
            credentials=get_credentials
        )

    @classmethod
    def update_config(cls, valid=None):
        preferences = Dict['preferences'] or {}

        # If no validation provided, use last stored result or assume true
        if valid is None:
            valid = preferences.get('valid', True)

        preferences['valid'] = valid

        Configuration.process(preferences)

        # Ensure preferences dictionary is stored
        Dict['preferences'] = preferences
        Dict.Save()

        log.info('Preferences updated %s', preferences)
        EventManager.fire('preferences.updated', preferences)

    @classmethod
    def validate_auth(cls, retry_interval=30):
        if not Prefs['username'] or not Prefs['password']:
            log.warn('Authentication failed, username or password field empty')

            cls.update_config(False)
            return False

        success = Trakt['account'].test()

        if not success:
            # status - False = invalid credentials, None = request failed
            if success is False:
                log.warn('Authentication failed, username or password is incorrect')
            else:
                # Increase retry interval each time to a maximum of 30 minutes
                if retry_interval < 60 * 30:
                    retry_interval = int(retry_interval * 1.3)

                # Ensure we never go over 30 minutes
                if retry_interval > 60 * 30:
                    retry_interval = 60 * 30

                log.warn('Unable to verify account details, will try again in %s seconds', retry_interval)
                schedule(cls.validate_auth, retry_interval, retry_interval)

            Main.update_config(False)
            return False

        log.info('Authentication successful')

        Main.update_config(True)
        return True

    def start(self):
        # Validate username/password
        spawn(self.validate_auth)

        # Check for updates
        self.update_checker.run_once(async=True)

        # TODO self.session_manager.start()

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
    last_activity_mode = get_pref('activity_mode')

    if Main.validate_auth():
        message = MessageContainer(
            "Success",
            "Authentication successful"
        )
    else:
        message = MessageContainer(
            "Error",
            "Authentication failed, incorrect username or password"
        )

    # Restart if activity_mode has changed
    if Prefs['activity_mode'] != last_activity_mode:
        log.info('Activity mode has changed, restarting plugin...')
        # TODO this can cause the preferences dialog to get stuck on "saving"
        #  - might need to delay this for a few seconds to avoid this.
        spawn(lambda: Plex[':/plugins'].restart(PLUGIN_IDENTIFIER))

    return message
