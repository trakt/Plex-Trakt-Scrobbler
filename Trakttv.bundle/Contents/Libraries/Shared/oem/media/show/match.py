from oem.media.show.identifier import EpisodeIdentifier


class EpisodeMatch(EpisodeIdentifier):
    def __init__(self, identifiers, season_num=None, episode_num=None, absolute_num=None, progress=None):
        super(EpisodeMatch, self).__init__(
            season_num=season_num,
            episode_num=episode_num,
            absolute_num=absolute_num,

            progress=progress
        )

        self.identifiers = identifiers or {}

    def __hash__(self):
        return hash((
            hash(frozenset(self.identifiers.items())),

            self.season_num,
            self.episode_num,
            self.absolute_num,
            self.progress
        ))

    def __repr__(self):
        fragments = []

        # Identifiers
        if self.identifiers:
            fragments.append('(' + (', '.join(('%s: %r' % (key, value)) for key, value in self.identifiers.items())) + ')')

            if self.absolute_num is not None or self.season_num is not None:
                fragments.append('-')

        # Absolute
        if self.absolute_num is not None:
            fragments.append('[%03d]' % self.absolute_num)

        # Season + Episode
        if self.season_num is not None and self.episode_num is not None:
            fragments.append('S%02dE%02d' % (self.season_num, self.episode_num))
        elif self.season_num is not None:
            fragments.append('S%02d' % self.season_num)

        # Attributes
        attributes = [
            ('%s: %r' % (key, getattr(self, key))) for key in ['progress'] if getattr(self, key)
        ]

        if attributes:
            fragments.append('(%s)' % (', '.join(attributes)))

        return '<%s%s>' % (
            self.__class__.__name__,
            (' %s' % (' '.join(fragments))) if fragments else ''
        )
