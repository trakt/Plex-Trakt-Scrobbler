from oem_framework.core.helpers import get_attribute
from oem_framework.models.core import BaseMedia

import logging

log = logging.getLogger(__name__)


class Movie(BaseMedia):
    __slots__ = ['names', 'mappings']
    __attributes__ = ['names', 'mappings']

    def __init__(self, collection, identifiers, names, mappings=None, **kwargs):
        super(Movie, self).__init__(collection, 'movie', identifiers, **kwargs)

        self.names = names or set()

        self.mappings = mappings or []

    @classmethod
    def from_dict(cls, collection, data, **kwargs):
        touched = set()

        # Construct movie
        movie = cls(
            collection,

            identifiers=get_attribute(touched, data, 'identifiers'),
            names=set(get_attribute(touched, data, 'names', [])),

            supplemental=get_attribute(touched, data, 'supplemental', {}),
            **get_attribute(touched, data, 'parameters', {})
        )

        # Ensure all attributes were touched
        omitted = [
            k for k in (set(data.keys()) - touched)
            if not k.startswith('_')
        ]

        if omitted:
            log.warn('Movie.from_dict() omitted %d attribute(s): %s', len(omitted), ', '.join(omitted))

        return movie

    def __repr__(self):
        if self.identifiers and self.names:
            service = self.identifiers.keys()[0]

            return '<Movie %s: %r, names: %r>' % (
                service,
                self.identifiers[service],
                self.names
            )

        if self.identifiers:
            service = self.identifiers.keys()[0]

            return '<Movie %s: %r>' % (
                service,
                self.identifiers[service]
            )

        if self.names:
            return '<Movie names: %r>' % (
                self.names
            )

        return '<Movie>'
