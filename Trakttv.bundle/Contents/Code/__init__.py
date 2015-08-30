# ------------------------------------------------
# Environment
# ------------------------------------------------
from plugin.core.environment import Environment
import locale
import os

Environment.setup(Core, Dict, Platform, Prefs)

# plex.database.py
os.environ['LIBRARY_DB'] = os.path.join(
    Environment.path.plugin_support, 'Databases',
    'com.plexapp.plugins.library.db'
)

# locale
try:
    Log.Debug('Using locale: %s', locale.setlocale(locale.LC_ALL, ''))
except Exception, ex:
    Log.Warn('Unable to update locale: %s', ex)
# ------------------------------------------------
# Libraries
# ------------------------------------------------
from libraries import Libraries

Libraries.setup(cache=True)
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

# Check "apsw" availability
try:
    import apsw

    Log.Debug('apsw: %r, sqlite: %r', apsw.apswversion(), apsw.SQLITE_VERSION_NUMBER)
except Exception, ex:
    Log.Error('Unable to import "apsw": %s', ex)

# Check "llist" availability
try:
    import llist

    Log.Debug('llist: available')
except Exception, ex:
    Log.Warn('Unable to import "llist": %s', ex)

# Local imports
from core.logger import Logger
from core.helpers import spawn
from core.plugin import ART, NAME, ICON
from main import Main

from plugin.api.core.manager import ApiManager
from plugin.core.constants import PLUGIN_IDENTIFIER
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
    ObjectContainer.art = R(ART)
    ObjectContainer.title1 = NAME
    DirectoryObject.thumb = R(ICON)
    DirectoryObject.art = R(ART)
    PopupDirectoryObject.thumb = R(ICON)
    PopupDirectoryObject.art = R(ART)

    if not Singleton.acquire():
        log.warn('Unable to acquire plugin instance')

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
    except Exception, ex:
        Log.Error('Unable to process API request (args: %r, kwargs: %r) - %s', args, kwargs, ex)
        return None


def ValidatePrefs():
    # Retrieve plex token
    token_plex = os.environ.get('PLEXTOKEN')

    if not token_plex:
        token_plex = Request.Headers.get('X-Plex-Token')

        if token_plex:
            log.debug('No plex token found in environment, using request token')
        else:
            data = {
                'Client': {
                    'User-Agent': Request.Headers.get('User-Agent'),
                    'X-Plex-Product': Request.Headers.get('X-Plex-Product'),
                },
                'Headers': Request.Headers.keys()
            }

            log.debug('Request details: %r', data)
            log.error('No plex token found in environment and request', extra={
                'data': data
            })

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
    if Preferences.get('activity.mode') != last_activity_mode:
        log.info('Activity mode has changed, restarting plugin...')

        def restart():
            # Delay until after `ValidatePrefs` returns
            time.sleep(3)

            # Restart plugin
            Plex[':/plugins'].restart(PLUGIN_IDENTIFIER)

        spawn(restart)
        return MessageContainer("Success", "Success")

    # Fire configuration changed callback
    spawn(Main.on_configuration_changed)

    return MessageContainer("Success", "Success")
