from plex_metadata.agents import Agents
from plex_metadata.core.helpers import urlparse

import logging

log = logging.getLogger(__name__)
unsupported_agents = {}


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
        # `sid` property always returns strings
        return str(self.id)

    @classmethod
    def construct(cls, service, id, extra=None):
        result = cls(id, extra)
        result.service = service
        result.id = id

        return result

    @classmethod
    def parse(cls, guid, match=True, media=None, strict=False):
        if not guid:
            return None

        # Parse Guid URI
        agent_name, uri = urlparse(guid)

        if not agent_name or not uri or not uri.netloc:
            return None

        # Construct `Guid` object
        result = Guid(uri.netloc, uri.query)

        # Match guid with agent, fill with details
        if match and cls.match(agent_name, result, uri, media):
            return result

        if strict:
            return None

        # No agent matching enabled, basic fill
        result.service = agent_name[agent_name.rfind('.') + 1:]
        result.id = uri.netloc

        return result

    @classmethod
    def match(cls, agent_name, guid, uri, media=None):
        # Retrieve `Agent` for provided `guid`
        agent = Agents.get(agent_name)

        if agent is None:
            if agent_name not in unsupported_agents:
                # First occurrence of unsupported agent
                log.warn('Unsupported metadata agent: %r' % agent_name)

                # Mark unsupported agent as "seen"
                unsupported_agents[agent_name] = True
                return False

            # Duplicate occurrence of unsupported agent
            log.warn('Unsupported metadata agent: %r' % agent_name, extra={
                'duplicate': True
            })
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
