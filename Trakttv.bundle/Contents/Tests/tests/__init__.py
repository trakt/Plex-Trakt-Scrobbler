import logging
logging.basicConfig(level=logging.DEBUG)

import os
import sys
import tempfile

#
# Directories / Paths
#

CURRENT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')

# Build plugin paths
CODE_DIR = os.path.abspath(os.path.join(CURRENT_DIR, '..', 'Code'))
LIBRARIES_DIR = os.path.abspath(os.path.join(CURRENT_DIR, '..', 'Libraries'))
PLUGIN_DIR = os.path.abspath(os.path.join(LIBRARIES_DIR, 'Shared', 'plugin'))

# Create temporary directory
TEMP_DIR = tempfile.mkdtemp()

# Update `sys.path`
sys.path.insert(0, os.path.join(LIBRARIES_DIR, 'Shared'))
sys.path.insert(0, CODE_DIR)

#
# Environment
#

from plex_mock.framework import Core
from plugin.core.environment import Environment
from plugin.core.constants import PLUGIN_IDENTIFIER

# Setup environment
Environment.setup(Core(CODE_DIR), {
    'trakt.token': 'trakt.token'
}, None, {
    'username': 'username',
    'password': 'password'
})

# Build directory structure for "Plug-in Support"
PLUGIN_SUPPORT = os.path.join(TEMP_DIR, 'Plug-in Support')

os.makedirs(os.path.join(PLUGIN_SUPPORT, 'Caches', PLUGIN_IDENTIFIER))
os.makedirs(os.path.join(PLUGIN_SUPPORT, 'Data', PLUGIN_IDENTIFIER))
os.makedirs(os.path.join(PLUGIN_SUPPORT, 'Databases'))

Environment.path.plugin_support = PLUGIN_SUPPORT

# Setup native libraries
from plugin.core.libraries.manager import LibrariesManager

LibrariesManager.setup(cache=False)
LibrariesManager.test()

# Setup database proxy
from plugin.core.database.manager import DatabaseManager
from tests.helpers.database import DATABASE_PROXY

db_path = os.path.abspath(Environment.path.plugin_database)

DatabaseManager._cache['peewee'][db_path] = DATABASE_PROXY

# Configure plex.database.py
os.environ['LIBRARY_DB'] = os.path.join(
    Environment.path.plugin_support, 'Databases',
    'com.plexapp.plugins.library.db'
)

#
# Preferences
#

from plugin.preferences.main import Preferences

@classmethod
def preferences_get(cls, key, account=None):
    return None

# Patch `Preferences.get` method
Preferences.get = preferences_get

#
# Modules
#

from plugin.core.importer import import_modules
from plugin.modules.core.manager import ModuleManager

# ModuleManager
ModuleManager.initialize()
ModuleManager.start([
    'matcher'
])

# Scrobbler
import_modules(os.path.join(PLUGIN_DIR, 'scrobbler', 'handlers'), exclude=[
    '__init__.py'
])
