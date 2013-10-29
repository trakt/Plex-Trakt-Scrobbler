import sys

# Modules???

import plugin
sys.modules['core.plugin'] = plugin

import header
sys.modules['core.header'] = header

import helpers
sys.modules['core.helpers'] = helpers

import eventing
sys.modules['core.eventing'] = eventing

import http
sys.modules['core.http'] = http

import pms
sys.modules['core.pms'] = pms

import trakt
sys.modules['core.trakt'] = trakt

import update_checker
sys.modules['core.update_checker'] = update_checker
