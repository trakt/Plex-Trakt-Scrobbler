from oem.media.movie.identifier import MovieIdentifier


class MovieMatch(MovieIdentifier):
    def __init__(self, identifiers, progress=None):
        super(MovieMatch, self).__init__(progress)

        self.identifiers = identifiers or {}

    def __eq__(self, other):
        if not other:
            return False

        return (
            self.identifiers  == other.identifiers and
            self.progress     == other.progress
        )

    def __repr__(self):
        fragments = []

        # Identifiers
        if self.identifiers:
            fragments.append('(' + (', '.join(('%s: %r' % (key, value)) for key, value in self.identifiers.items())) + ')')

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
