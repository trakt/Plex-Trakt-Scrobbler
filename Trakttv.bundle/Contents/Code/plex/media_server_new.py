from core.helpers import all
from core.logger import Logger
from plex.plex_base import PlexBase

log = Logger('plex.media_server_new')


class PlexMediaServer(PlexBase):
    @classmethod
    def get_server_info(cls, quiet=False):
        return cls.request(quiet=quiet)

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
        result = cls.request(
            ':/rate?key=%s&identifier=com.plexapp.plugins.library&rating=%s' % (key, value),
            response_type='text'
        )

        return result is not None
