import sys

# submodules for Plex plugins "hack"

import plugin
sys.modules['core.plugin'] = plugin

import logger
sys.modules['core.logger'] = logger

import localization
sys.modules['core.localization'] = localization

import logging_reporter
sys.modules['core.logging_reporter'] = logging_reporter

import logging_handler
sys.modules['core.logging_handler'] = logging_handler

import header
sys.modules['core.header'] = header

import helpers
sys.modules['core.helpers'] = helpers

import cache
sys.modules['core.cache'] = cache

import configuration
sys.modules['core.configuration'] = configuration

import update_checker
sys.modules['core.update_checker'] = update_checker

import migrator
sys.modules['core.migrator'] = migrator
