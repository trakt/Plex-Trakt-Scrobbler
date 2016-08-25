from plex_metadata import Guid


class GuidMatch(object):
    class Media(object):
        __options__ = [
            'episode',
            'movie'
        ]

        Episode = 'episode'
        Movie   = 'movie'

    def __init__(self, media, guid, episodes=None, supported=False, found=False, invalid=False):
        self.media = media
        self.guid = guid

        # Episode
        self.episodes = episodes

        # Flags
        self.supported = supported
        self.found = found
        self.invalid = invalid

        # Validate parameters
        if not self.media or self.media not in GuidMatch.Media.__options__:
            raise ValueError('Invalid value provided for the "media" parameter: %r' % (media,))

        if guid and not isinstance(guid, Guid):
            raise ValueError('Invalid value provided for the "guid" parameter: %r' % (guid,))

    @property
    def table_key(self):
        if self.media == GuidMatch.Media.Episode:
            return 'shows'

        if self.media == GuidMatch.Media.Movie:
            return 'movies'

        raise ValueError('Unknown media type: %r' % (self.media,))

    @property
    def valid(self):
        if self.invalid:
            return False

        if not self.media or self.media not in GuidMatch.Media.__options__:
            return False

        return self.supported and self.found
