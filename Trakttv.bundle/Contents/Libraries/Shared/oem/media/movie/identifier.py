from oem.media.core.base.identifier import Identifier


class MovieIdentifier(Identifier):
    def __init__(self, progress=None):
        self.progress = progress

    @property
    def valid(self):
        return True

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
