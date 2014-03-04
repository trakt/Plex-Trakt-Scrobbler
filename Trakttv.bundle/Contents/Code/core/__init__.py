import sys

# submodules for Plex plugins "hack"

import plugin
sys.modules['core.plugin'] = plugin

import logger
sys.modules['core.logger'] = logger

import header
sys.modules['core.header'] = header


import model
sys.modules['core.model'] = model

import helpers
sys.modules['core.helpers'] = helpers

import eventing
sys.modules['core.eventing'] = eventing

import cache
sys.modules['core.cache'] = cache

import network
sys.modules['core.network'] = network

import method_manager
sys.modules['core.method_manager'] = method_manager

import trakt_objects
sys.modules['core.trakt_objects'] = trakt_objects

import trakt
sys.modules['core.trakt'] = trakt

import update_checker
sys.modules['core.update_checker'] = update_checker

import migrator
sys.modules['core.migrator'] = migrator

import task
sys.modules['core.task'] = task
