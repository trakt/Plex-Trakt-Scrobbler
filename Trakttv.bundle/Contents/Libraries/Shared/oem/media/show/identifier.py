from oem.media.core.base.identifier import Identifier


class EpisodeIdentifier(Identifier):
    __slots__ = ['season_num', 'episode_num', 'absolute_num', 'progress']

    def __init__(self, season_num=None, episode_num=None, absolute_num=None, progress=None, part=None):
        # Season + Episode Identifier
        self.season_num = season_num
        self.episode_num = episode_num

        # Absolute Identifier
        self.absolute_num = absolute_num

        # Extra
        self.progress = progress
        self.part = part

    @property
    def valid(self):
        return (
            self.season_num is not None and
            self.episode_num is not None
        ) or (
            self.absolute_num is not None
        )

    def to_dict(self):
        result = {}

        if self.absolute_num is not None:
            result['absolute_num'] = self.absolute_num

        if self.season_num is not None:
            result['season_num'] = self.season_num

        if self.episode_num is not None:
            result['episode_num'] = self.episode_num

        if self.progress is not None:
            result['progress'] = self.progress

        if self.part is not None:
            result['part'] = self.part

        return result

    def to_frozenset(self, data=None):
        if data is None:
            data = self.to_dict()

        if type(data) is dict:
            data = data.items()

        result = []

        for item in data:
            if type(item) is tuple and len(item) == 2:
                key, value = item
            else:
                key = None
                value = item

            if type(value) is dict:
                value = self.to_frozenset(value)

            if type(value) is list:
                value = self.to_frozenset(value)

            if key is not None:
                result.append((key, value))
            else:
                result.append(value)

        return frozenset(result)

    def __hash__(self):
        return hash(self.to_frozenset())

    def __eq__(self, other):
        if not other:
            return False

        return self.__hash__() == other.__hash__()

    def __ne__(self, other):
        return not(self == other)

    def __repr__(self):
        attributes = [
            ('%s: %r' % (key, getattr(self, key)))
            for key in ['progress', 'part'] if getattr(self, key)
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
