from __future__ import absolute_import, division, print_function

from oem.media.core.base.identifier import Identifier


class MovieIdentifier(Identifier):
    def __init__(self, part=None, progress=None):
        self.part = part

        self.progress = progress

    @property
    def valid(self):
        return True

    def to_dict(self):
        result = {}

        if self.progress is not None:
            result['progress'] = self.progress

        return result

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
