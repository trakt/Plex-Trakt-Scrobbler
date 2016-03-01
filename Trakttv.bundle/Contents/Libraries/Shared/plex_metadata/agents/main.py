from plex_metadata.agents.agent import Agent
from plex_metadata.agents.entries import AGENTS

import logging

log = logging.getLogger(__name__)


class Agents(object):
    __agents = {}
    __compiled = False

    @classmethod
    def compile(cls):
        if cls.__compiled:
            return

        log.debug('Compiling agents...')

        for key, entry in AGENTS.items():
            cls.__agents[key] = Agent.compile(entry)

        cls.__compiled = True

        log.debug('Compiled %d agents', len(cls.__agents))

    @classmethod
    def get(cls, key):
        # Ensure agents have been compiled
        cls.compile()

        # Try find compiled agent
        return cls.__agents.get(key)
