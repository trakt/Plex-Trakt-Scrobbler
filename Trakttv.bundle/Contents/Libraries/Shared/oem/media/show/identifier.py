from oem.media.core.base.identifier import Identifier


class EpisodeIdentifier(Identifier):
    __slots__ = ['season_num', 'episode_num', 'absolute_num', 'progress']

    def __init__(self, season_num=None, episode_num=None, absolute_num=None, progress=None):
        # Season + Episode Identifier
        self.season_num = season_num
        self.episode_num = episode_num

        # Absolute Identifier
        self.absolute_num = absolute_num

        # Extra
        self.progress = progress

    @property
    def valid(self):
        return (self.season_num is not None and self.episode_num is not None) or self.absolute_num is not None

    def __hash__(self):
        return hash((
            self.season_num,
            self.episode_num,
            self.absolute_num,
            self.progress
        ))

    def __eq__(self, other):
        if not other:
            return False

        return self.__hash__() == other.__hash__()

    def __ne__(self, other):
        return not(self == other)

    def __repr__(self):
        attributes = [
            ('%s: %r' % (key, getattr(self, key))) for key in ['progress'] if getattr(self, key)
        ]

        fragments = []

        if self.absolute_num:
            fragments.append('[%03d]' % self.absolute_num)

        if self.season_num is not None and self.episode_num is not None:
            fragments.append('S%02dE%02d' % (self.season_num, self.episode_num))
        elif self.season_num is not None:
            fragments.append('S%02d' % self.season_num)

        if attributes:
            fragments.append('(%s)' % (', '.join(attributes)))

        return '<%s%s>' % (
            self.__class__.__name__,
            (' %s' % (' '.join(fragments))) if fragments else ''
        )
