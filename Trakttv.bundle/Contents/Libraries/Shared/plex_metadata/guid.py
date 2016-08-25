from plex_metadata.agents import Agents
from plex_metadata.core.helpers import urlparse

import logging

log = logging.getLogger(__name__)
unsupported_agents = {}


class Guid(object):
    def __init__(self, value=None, extra=None, matched=False, invalid=False, agent_id=None, original=None):
        self.value = value
        self.extra = extra

        self.matched = matched
        self.invalid = invalid

        self.agent_id = agent_id
        self.original = original

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

    @property
    def valid(self):
        return not self.invalid and self.matched

    @classmethod
    def construct(cls, service, id, extra=None, matched=False, invalid=False):
        result = cls(
            id, extra,
            matched=matched,
            invalid=invalid
        )

        result.service = service
        result.id = id
        return result

    @classmethod
    def parse(cls, guid, match=True, media=None, strict=False):
        if not guid:
            return cls(
                invalid=True,
                original=guid
            )

        # Parse Guid URI
        agent_id, uri = urlparse(guid)

        if not agent_id or not uri or not uri.netloc:
            return cls(
                invalid=True,
                agent_id=agent_id,
                original=guid
            )

        # Construct `Guid` object
        result = cls(
            uri.netloc,
            extra=uri.query,

            agent_id=agent_id,
            original=guid
        )

        # Match guid with agent, fill with details
        if match and cls.match(agent_id, result, uri, media):
            result.matched = True
            return result

        if strict:
            return result

        # No agent matching enabled, automatically match guid parameters
        log.warn('Unable to find agent mapping for %s://%s, result may be incorrect', agent_id, uri.netloc)

        result.service = agent_id[agent_id.rfind('.') + 1:]
        result.id = uri.netloc
        return result

    @classmethod
    def match(cls, agent_name, guid, uri, media=None):
        # Retrieve `Agent` for provided `guid`
        agent = Agents.get(agent_name)

        if agent is None:
            if agent_name not in unsupported_agents:
                # First occurrence of unsupported agent
                log.warn('Unsupported metadata agent: %s' % agent_name)

                # Mark unsupported agent as "seen"
                unsupported_agents[agent_name] = True
                return False

            # Duplicate occurrence of unsupported agent
            log.warn('Unsupported metadata agent: %s' % agent_name, extra={
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
