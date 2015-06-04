import sys


import sync_menu
sys.modules['interface.sync_menu'] = sync_menu

import main_menu
sys.modules['interface.main_menu'] = main_menu

import resources
sys.modules['interface.resources'] = resources
