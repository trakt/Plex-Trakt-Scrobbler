from core.helpers import all
from core.logger import Logger
from plex.plex_base import PlexBase

log = Logger('plex.plex_media_server')


class PlexMediaServer(PlexBase):
    #
    # Server
    #

    @classmethod
    def get_info(cls, quiet=False):
        return cls.request(quiet=quiet)

    @classmethod
    def get_version(cls, default=None, quiet=False):
        server_info = cls.get_info(quiet)
        if server_info is None:
            return default

        return server_info.attrib.get('version') or default

    @classmethod
    def get_client(cls, client_id):
        if not client_id:
            log.warn('Invalid client_id provided')
            return None

        result = cls.request('clients')
        if not result:
            return None

        found_clients = []

        for section in result.xpath('//Server'):
            found_clients.append(section.get('machineIdentifier'))

            if section.get('machineIdentifier') == client_id:
                return section

        log.info("Unable to find client '%s', available clients: %s" % (client_id, found_clients))
        return None

    @classmethod
    def get_sessions(cls):
        return cls.request('status/sessions')

    @classmethod
    def get_session(cls, session_key):
        sessions = cls.get_sessions()
        if sessions is None:
            log.warn('Sessions request failed')
            return None

        for section in sessions.xpath('//MediaContainer/Video'):
            if section.get('sessionKey') == session_key and '/library/metadata' in section.get('key'):
                return section

        log.warn('Session "%s" not found', session_key)
        return None

    #
    # Collection
    #

    @classmethod
    def get_sections(cls, types=None, keys=None, cache_id=None):
        """Get the current sections available on the server, optionally filtering by type and/or key

        :param types: Section type filter
        :type types: str or list of str

        :param keys: Section key filter
        :type keys: str or list of str

        :return: List of sections found
        :rtype: (type, key, title)
        """

        if types and isinstance(types, basestring):
            types = [types]

        if keys and isinstance(keys, basestring):
            keys = [keys]

        container = cls.request('library/sections', cache_id=cache_id)

        sections = []
        for section in container:
            # Try retrieve section details - (type, key, title)
            section = (
                section.get('type', None),
                section.get('key', None),
                section.get('title', None)
            )

            # Validate section, skip over bad sections
            if not all(x for x in section):
                continue

            # Apply key filter
            if keys is not None and section[1] not in keys:
                continue

            # Apply type filter
            if types is not None and section[0] not in types:
                continue

            sections.append(section)

        return sections

    @classmethod
    def get_section(cls, key, cache_id=None):
        return cls.request('library/sections/%s/all' % key, timeout=10, cache_id=cache_id)

    @classmethod
    def get_directories(cls, key, cache_id=None):
        section = cls.get_section(key, cache_id=cache_id)
        if section is None:
            return []

        return section.xpath('//Directory')

    @classmethod
    def get_videos(cls, key, cache_id=None):
        section = cls.get_section(key, cache_id=cache_id)
        if section is None:
            return []

        return section.xpath('//Video')

    @classmethod
    def scrobble(cls, key):
        result = cls.request(
            ':/scrobble?identifier=com.plexapp.plugins.library&key=%s' % key,
            response_type='text'
        )

        return result is not None

    @classmethod
    def rate(cls, key, value):
        value = int(round(value, 0))

        result = cls.request(
            ':/rate?key=%s&identifier=com.plexapp.plugins.library&rating=%s' % (key, value),
            response_type='text'
        )

        return result is not None
