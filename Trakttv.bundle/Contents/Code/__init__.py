# ------------------------------------------------
# Environment
# ------------------------------------------------
from plugin.core.environment import Environment

Environment.setup(Core, Dict, Prefs)
# ------------------------------------------------
# Modules
# ------------------------------------------------
import core
import interface
# ------------------------------------------------
# Handlers
# ------------------------------------------------
from interface.main_menu import MainMenu
# ------------------------------------------------

# Check "apsw" availability, log any errors
try:
    import apsw

    Log.Debug('apsw: %r, sqlite: %r', apsw.apswversion(), apsw.SQLITE_VERSION_NUMBER)
except Exception, ex:
    Log.Error('Unable to import "apsw": %s', ex)

# Local imports
from core.logger import Logger
from core.helpers import spawn, get_pref
from core.plugin import ART, NAME, ICON
from main import Main

from plugin.api.core.manager import ApiManager
from plugin.core.configuration import Configuration
from plugin.core.constants import PLUGIN_IDENTIFIER

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
    for key in Configuration.handlers.keys():
        Configuration.process(key, Prefs[key])

    last_activity_mode = get_pref('activity_mode')

    # Restart if activity_mode has changed
    if Prefs['activity_mode'] != last_activity_mode:
        log.info('Activity mode has changed, restarting plugin...')

        def restart():
            # Delay until after `ValidatePrefs` returns
            time.sleep(3)

            # Restart plugin
            Plex[':/plugins'].restart(PLUGIN_IDENTIFIER)

        spawn(restart)
        return MessageContainer("Success", "Success")

    # Re-initialize modules
    Main.init_logging()

    return MessageContainer("Success", "Success")
