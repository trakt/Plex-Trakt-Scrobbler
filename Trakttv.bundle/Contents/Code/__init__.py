# ------------------------------------------------
# Environment
# ------------------------------------------------
from plugin.core.environment import Environment
import locale
import os

Environment.setup(Core, Dict, Prefs)

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

# Check "apsw" availability, log any errors
try:
    import apsw

    Log.Debug('apsw: %r, sqlite: %r', apsw.apswversion(), apsw.SQLITE_VERSION_NUMBER)
except Exception, ex:
    Log.Error('Unable to import "apsw": %s', ex)

# Local imports
from core.logger import Logger
from core.helpers import spawn
from core.plugin import ART, NAME, ICON
from main import Main

from plugin.api.core.manager import ApiManager
from plugin.core.constants import PLUGIN_IDENTIFIER
from plugin.core.helpers.variable import get_pref
from plugin.preferences import OPTIONS_BY_PKEY, Preferences

from plex import Plex
import time


log = Logger()


def Start():
    ObjectContainer.art = R(ART)
    ObjectContainer.title1 = NAME
    DirectoryObject.thumb = R(ICON)
    DirectoryObject.art = R(ART)
    PopupDirectoryObject.thumb = R(ICON)
    PopupDirectoryObject.art = R(ART)

    m = Main()
    m.start()


@expose
def Api(*args, **kwargs):
    try:
        return ApiManager.process(
            Request.Method,
            Request.Headers,
            Request.Body,

            *args, **kwargs
        )
    except Exception, ex:
        Log.Error('Unable to process API request (args: %r, kwargs: %r) - %s', args, kwargs, ex)
        return None


def ValidatePrefs():
    # Process configuration changes
    for key in OPTIONS_BY_PKEY.keys():
        Preferences.on_plex_changed(key, Prefs[key])

    # Restart if activity_mode has changed
    last_activity_mode = get_pref('activity_mode')

    if Prefs['activity_mode'] != last_activity_mode:
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
