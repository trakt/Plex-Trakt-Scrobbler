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
import requests
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


def GetToken():
    # Environment token
    env_token = os.environ.get('PLEXTOKEN')

    if env_token:
        log.info('Plex Token: environment')
        return env_token

    # Check if anonymous access is available
    server = requests.get('http://localhost:32400')

    if server.status_code == 200:
        log.info('Plex Token: anonymous')
        return 'anonymous'

    # Request token
    req_token = Request.Headers.get('X-Plex-Token')

    if req_token:
        log.info('Plex Token: request')
        return req_token

    # No token available
    data = {
        'Client': {
            'User-Agent': Request.Headers.get('User-Agent'),
            'X-Plex-Product': Request.Headers.get('X-Plex-Product'),
        },
        'Headers': Request.Headers.keys()
    }

    log.debug('Request details: %r', data)
    log.error('Plex Token: not available', extra={
        'data': data
    })
    return None


def ValidatePrefs():
    # Retrieve plex token
    token_plex = GetToken()

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
