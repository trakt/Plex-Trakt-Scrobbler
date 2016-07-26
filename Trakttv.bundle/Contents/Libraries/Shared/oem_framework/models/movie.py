from oem_framework.core.helpers import get_attribute
from oem_framework.models.core import BaseMedia

import logging

from oem_framework.models.core import ModelRegistry

log = logging.getLogger(__name__)


class Movie(BaseMedia):
    __slots__ = ['names', 'mappings', 'parts']
    __attributes__ = ['names', 'mappings', 'parts']

    def __init__(self, collection, identifiers, names, mappings=None, parts=None, **kwargs):
        super(Movie, self).__init__(collection, 'movie', identifiers, **kwargs)

        self.names = self._parse_names(collection, identifiers, names) or {}

        self.mappings = mappings or []
        self.parts = parts or {}

    def to_dict(self, key=None, flatten=True):
        result = super(Movie, self).to_dict(key=key, flatten=flatten)

        if not flatten:
            return result

        # Flatten "names" attribute
        self._flatten_names(self.collection, result)

        return result

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

        # Construct seasons
        if 'parts' in data:
            movie.parts = dict([
                (k, ModelRegistry['Part'].from_dict(collection, v, key=k, parent=movie))
                for k, v in get_attribute(touched, data, 'parts').items()
            ])

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
            service = list(self.identifiers.keys())[0]

            return '<Movie %s: %r, names: %r>' % (
                service,
                self.identifiers[service],
                self.names
            )

        if self.identifiers:
            service = list(self.identifiers.keys())[0]

            return '<Movie %s: %r>' % (
                service,
                self.identifiers[service]
            )

        if self.names:
            return '<Movie names: %r>' % (
                self.names
            )

        return '<Movie>'
