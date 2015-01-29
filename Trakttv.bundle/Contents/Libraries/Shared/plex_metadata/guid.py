from plex_metadata.core.defaults import DEFAULT_GUID_MAP, DEFAULT_TV_AGENTS
from plex_metadata.core.helpers import try_convert, compile_map, urlparse

import logging

log = logging.getLogger(__name__)


class Guid(object):
    map = compile_map(DEFAULT_GUID_MAP)

    def __init__(self, agent, sid, extra):
        self.agent = agent
        self.sid = sid
        self.extra = extra

        # Show
        self.season = None
        self.episode = None

    @classmethod
    def parse(cls, guid, map=True):
        if not guid:
            return None

        agent, uri = urlparse(guid)

        result = Guid(agent, uri.netloc, uri.query)

        # Nothing more to parse, return now
        if uri.path:
            cls.parse_path(result, uri)

        if map:
            return cls.map_guid(result)

        return result

    @classmethod
    def parse_path(cls, guid, uri):
        # Parse path component for agent-specific data
        path_fragments = uri.path.strip('/').split('/')

        if guid.agent in DEFAULT_TV_AGENTS:
            if len(path_fragments) >= 1:
                guid.season = try_convert(path_fragments[0], int)

            if len(path_fragments) >= 2:
                guid.episode = try_convert(path_fragments[1], int)
        else:
            log.warn('Unable to completely parse guid "%s"', guid)

    @classmethod
    def map_guid(cls, guid):
        agent, sid_pattern, match = cls.find_map(guid)

        guid.agent = agent

        # Match sid with regex
        if sid_pattern:
            if not match:
                log.warn('Failed to match "%s" against sid_pattern for "%s" agent', guid.sid, guid.agent)
                return None

            # Update with new sid
            guid.sid = ''.join(match.groups())

        return guid

    @classmethod
    def find_map(cls, guid):
        # Strip leading key
        agent = guid.agent[guid.agent.rfind('.') + 1:]

        # Return mapped agent and sid_pattern (if present)
        mappings = cls.map.get(agent, [])

        if type(mappings) is not list:
            mappings = [mappings]

        for mapping in mappings:
            map_agent, map_pattern = mapping

            if map_pattern is None:
                return map_agent, None, None

            match = map_pattern.match(guid.sid)
            if not match:
                continue

            return map_agent, map_pattern, match

        return agent, None, None
