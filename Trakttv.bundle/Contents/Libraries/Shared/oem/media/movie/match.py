from __future__ import absolute_import, division, print_function

from oem.media.movie.identifier import MovieIdentifier


class MovieMatch(MovieIdentifier):
    def __init__(self, identifiers, progress=None):
        super(MovieMatch, self).__init__(progress)

        self.identifiers = identifiers or {}

    def to_dict(self):
        result = super(MovieMatch, self).to_dict()

        result['identifiers'] = self.identifiers

        return result

    def __repr__(self):
        fragments = []

        # Identifiers
        if self.identifiers:
            fragments.append(
                '(' + (', '.join(
                    ('%s: %r' % (key, value))
                    for key, value in self.identifiers.items()
                )) + ')'
            )

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
