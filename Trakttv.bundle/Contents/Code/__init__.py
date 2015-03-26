# ------------------------------------------------
# Environment
# ------------------------------------------------
from plugin.core.environment import Environment

Environment.setup(Core, Dict, Prefs)
# ------------------------------------------------
# Modules
# ------------------------------------------------
import core
import data
import sync
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

from plugin.api.core.manager import ApiManager
from plugin.core.constants import PLUGIN_IDENTIFIER

from plex import Plex


log = Logger()


def Start():
    ObjectContainer.art = R(ART)
    ObjectContainer.title1 = NAME
    DirectoryObject.thumb = R(ICON)
    DirectoryObject.art = R(ART)

    from main import Main

    m = Main()
    m.start()


def ValidatePrefs():
    last_activity_mode = get_pref('activity_mode')

    # Restart if activity_mode has changed
    if Prefs['activity_mode'] != last_activity_mode:
        log.info('Activity mode has changed, restarting plugin...')
        # TODO this can cause the preferences dialog to get stuck on "saving"
        #  - might need to delay this for a few seconds to avoid this.
        spawn(lambda: Plex[':/plugins'].restart(PLUGIN_IDENTIFIER))

    return MessageContainer(
        "Success",
        "Success"
    )
