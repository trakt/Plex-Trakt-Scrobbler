from plex_metadata.agents import Agents
from plex_metadata.core.helpers import urlparse

import logging

log = logging.getLogger(__name__)


class Guid(object):
    def __init__(self, value, extra=None):
        self.value = value
        self.extra = extra

        # Identifier
        self.service = None
        self.id = None

        # Show
        self.season = None
        self.episode = None

        # Optional
        self.language = None

    @property
    def agent(self):
        return self.service

    @property
    def sid(self):
        return self.id

    @classmethod
    def parse(cls, guid, match=True, media=None):
        if not guid:
            return None

        # Parse Guid URI
        agent_name, uri = urlparse(guid)

        if not agent_name or not uri or not uri.netloc:
            return None

        # Construct `Guid` object
        result = Guid(uri.netloc, uri.query)

        if not match:
            # No agent matching enabled, basic fill
            result.service = agent_name[agent_name.rfind('.') + 1:]
            result.id = uri.netloc

            return result

        # Match guid with agent, fill with details
        if not cls.match(agent_name, result, uri, media):
            return None

        return result

    @classmethod
    def match(cls, agent_name, guid, uri, media=None):
        # Retrieve `Agent` for provided `guid`
        agent = Agents.get(agent_name)

        if agent is None:
            log.warn('Unsupported metadata agent: %r', agent_name)
            return False

        # Fill `guid` with details from agent
        return agent.fill(guid, uri, media)

    def __repr__(self):
        parameters = [
            'service: %r' % self.service,
            'id: %r' % self.id
        ]

        if self.season is not None:
            parameters.append('season: %r' % self.season)

        if self.episode is not None:
            parameters.append('episode: %r' % self.episode)

        return '<Guid - %s>' % ', '.join(parameters)

    def __str__(self):
        return self.__repr__()
