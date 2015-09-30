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

from tests.mock.framework import Core
from plugin.core.environment import Environment
from plugin.core.constants import PLUGIN_IDENTIFIER

# Setup environment
Environment.setup(Core(CODE_DIR), {
    'trakt.token': 'trakt.token'
}, None, {
    'username': 'username',
    'password': 'password'
})

# Setup native libraries
from libraries import Libraries

Libraries.setup()

# Build directory structure for "Plug-in Support"
PLUGIN_SUPPORT = os.path.join(TEMP_DIR, 'Plug-in Support')

os.makedirs(os.path.join(PLUGIN_SUPPORT, 'Caches', PLUGIN_IDENTIFIER))
os.makedirs(os.path.join(PLUGIN_SUPPORT, 'Data', PLUGIN_IDENTIFIER))
os.makedirs(os.path.join(PLUGIN_SUPPORT, 'Databases'))

Environment.path.plugin_support = PLUGIN_SUPPORT

# Configure plex.database.py
os.environ['LIBRARY_DB'] = os.path.join(
    Environment.path.plugin_support, 'Databases',
    'com.plexapp.plugins.library.db'
)

#
# Modules
#

from plugin.core.importer import import_modules

import_modules(os.path.join(PLUGIN_DIR, 'scrobbler', 'handlers'), exclude=[
    '__init__.py'
])
