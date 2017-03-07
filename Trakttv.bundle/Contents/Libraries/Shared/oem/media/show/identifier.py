from __future__ import absolute_import, division, print_function

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
