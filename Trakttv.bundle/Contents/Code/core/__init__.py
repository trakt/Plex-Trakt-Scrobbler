import sys

# submodules for Plex plugins "hack"

import plugin
sys.modules['core.plugin'] = plugin

import logger
sys.modules['core.logger'] = logger

import localization
sys.modules['core.localization'] = localization

import header
sys.modules['core.header'] = header

import helpers
sys.modules['core.helpers'] = helpers

import update_checker
sys.modules['core.update_checker'] = update_checker
