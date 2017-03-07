from __future__ import absolute_import, division, print_function

from oem.media.show.identifier import EpisodeIdentifier


class EpisodeMatch(EpisodeIdentifier):
    def __init__(self, identifiers, season_num=None, episode_num=None, absolute_num=None,
                 progress=None, part=None, mappings=None):

        super(EpisodeMatch, self).__init__(
            season_num=season_num,
            episode_num=episode_num,
            absolute_num=absolute_num,

            progress=progress,
            part=part
        )

        self.identifiers = identifiers or {}
        self.mappings = mappings or []

    @property
    def valid(self):
        return len(self.identifiers) > 0 and (
            super(EpisodeMatch, self).valid or
            len(self.mappings) > 0
        )

    def to_dict(self):
        result = super(EpisodeMatch, self).to_dict()

        result['identifiers'] = self.identifiers

        if self.mappings:
            result['mappings'] = [m.to_dict(compact=False) for m in self.mappings]

        return result

    def __repr__(self):
        fragments = []

        # Identifiers
        if self.identifiers:
            fragments.append(
                '(' + (', '.join(
                    ('%s: %r' % (key, value)) for key, value in self.identifiers.items()
                )) + ')'
            )

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
