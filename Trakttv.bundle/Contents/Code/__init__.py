# ------------------------------------------------
# Environment
# ------------------------------------------------
from plugin.core.environment import Environment, translate as _
import os

Environment.setup(Core, Dict, Platform, Prefs)

# plex.database.py
os.environ['LIBRARY_DB'] = os.path.join(
    Environment.path.plugin_support, 'Databases',
    'com.plexapp.plugins.library.db'
)

# ------------------------------------------------
# FS Migrator
# ------------------------------------------------
from fs_migrator import FSMigrator

FSMigrator.run()

# ------------------------------------------------
# Logger
# ------------------------------------------------

from plugin.core.logger import LoggerManager

LoggerManager.setup(storage=False)

# ------------------------------------------------
# Interface messages
# ------------------------------------------------

from plugin.core.message import InterfaceMessages

InterfaceMessages.bind()

# ------------------------------------------------
# Language
# ------------------------------------------------
Environment.setup_locale()
Environment.setup_translation()
# ------------------------------------------------
# Libraries
# ------------------------------------------------
from plugin.core.libraries.manager import LibrariesManager

LibrariesManager.setup(cache=True)
LibrariesManager.test()
# ------------------------------------------------
# Warnings
# ------------------------------------------------
from requests.packages.urllib3.exceptions import InsecurePlatformWarning, SNIMissingWarning
import warnings

warnings.filterwarnings('once', category=InsecurePlatformWarning)
warnings.filterwarnings('once', category=SNIMissingWarning)
# ------------------------------------------------
# Modules
# ------------------------------------------------
import core
import interface
# ------------------------------------------------
# Handlers
# ------------------------------------------------
from interface.m_main import MainMenu
from interface.resources import Cover, Thumb
# ------------------------------------------------

# Local imports
from core.logger import Logger
from core.helpers import spawn
from main import Main

from plugin.api.core.manager import ApiManager
from plugin.core.constants import PLUGIN_NAME, PLUGIN_ART, PLUGIN_ICON, PLUGIN_IDENTIFIER
from plugin.core.singleton import Singleton
from plugin.models.account import Account
from plugin.modules.migrations.account import AccountMigration
from plugin.preferences import Preferences

from datetime import datetime
from plex import Plex
import json
import time

# http://bugs.python.org/issue7980
datetime.strptime('', '')

log = Logger()


def Start():
    ObjectContainer.art = R(PLUGIN_ART)
    ObjectContainer.title1 = PLUGIN_NAME
    DirectoryObject.thumb = R(PLUGIN_ICON)
    DirectoryObject.art = R(PLUGIN_ART)
    PopupDirectoryObject.thumb = R(PLUGIN_ICON)
    PopupDirectoryObject.art = R(PLUGIN_ART)

    if not Singleton.acquire():
        log.warn('Unable to acquire plugin instance')

    # Complete logger initialization
    LoggerManager.setup(storage=True)

    # Store current proxy details
    Dict['proxy_host'] = Prefs['proxy_host']

    Dict['proxy_username'] = Prefs['proxy_username']
    Dict['proxy_password'] = Prefs['proxy_password']

    # Store current language
    Dict['language'] = Prefs['language']

    # Start plugin
    m = Main()
    m.start()


@expose
def Api(*args, **kwargs):
    try:
        data = ApiManager.process(
            Request.Method,
            Request.Headers,
            Request.Body,

            *args, **kwargs
        )

        return json.dumps(data)
    except Exception as ex:
        Log.Error('Unable to process API request (args: %r, kwargs: %r) - %s', args, kwargs, ex)
        return None


def ValidatePrefs():
    # Retrieve plex token
    token_plex = AccountMigration.get_token(Request.Headers)

    # Retrieve current activity mode
    last_activity_mode = Preferences.get('activity.mode')

    if Request.Headers.get('X-Disable-Preference-Migration', '0') == '0':
        # Run account migration
        am = AccountMigration()
        am.run(token_plex)

        # Migrate server preferences
        Preferences.migrate()

        # Try migrate administrator preferences
        try:
            Preferences.initialize(account=1)
            Preferences.migrate(account=1)
        except Account.DoesNotExist:
            log.debug('Unable to migrate administrator preferences, no account found')
    else:
        log.debug('Ignoring preference migration (disabled by header)')

    # Restart if activity_mode has changed
    if RestartRequired(last_activity_mode):
        log.info('Restart required to apply changes, restarting plugin...')

        def restart():
            # Delay until after `ValidatePrefs` returns
            time.sleep(3)

            # Restart plugin
            Plex[':/plugins'].restart(PLUGIN_IDENTIFIER)

        spawn(restart, daemon=True)
        return MessageContainer(_("Success"), _("Success"))

    # Fire configuration changed callback
    spawn(Main.on_configuration_changed, daemon=True)

    return MessageContainer(_("Success"), _("Success"))


def RestartRequired(last_activity_mode):
    if Preferences.get('activity.mode') != last_activity_mode:
        return True

    for key in ['language', 'proxy_host', 'proxy_username', 'proxy_password']:
        if Prefs[key] != Dict[key]:
            return True

    return False
