from oem.media.core.base.identifier import Identifier


class MovieIdentifier(Identifier):
    def __init__(self, progress=None):
        self.progress = progress

    @property
    def valid(self):
        return True

    def __hash__(self):
        return hash((
            self.progress,
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

        if attributes:
            fragments.append('(%s)' % (', '.join(attributes)))

        return '<%s%s>' % (
            self.__class__.__name__,
            (' %s' % (' '.join(fragments))) if fragments else ''
        )
