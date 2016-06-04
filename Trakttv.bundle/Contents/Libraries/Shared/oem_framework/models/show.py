from oem_framework.core.helpers import get_attribute
from oem_framework.models.core import BaseMedia, ModelRegistry

import logging

log = logging.getLogger(__name__)


class Show(BaseMedia):
    __slots__ = ['names', 'mappings', 'seasons']
    __attributes__ = ['names', 'mappings', 'seasons']

    def __init__(self, collection, identifiers, names, mappings=None, seasons=None, **kwargs):
        super(Show, self).__init__(collection, 'show', identifiers, **kwargs)

        self.names = self._parse_names(collection, identifiers, names) or {}

        self.mappings = mappings or []
        self.seasons = seasons or {}

    def to_dict(self, key=None, flatten=True):
        result = super(Show, self).to_dict(key=key, flatten=flatten)

        if not flatten:
            return result

        # Flatten "names" attribute
        self._flatten_names(self.collection, result)

        return result

    @classmethod
    def from_dict(cls, collection, data, **kwargs):
        touched = set()

        # Construct movie
        show = cls(
            collection,

            identifiers=get_attribute(touched, data, 'identifiers'),
            names=set(get_attribute(touched, data, 'names', [])),

            supplemental=get_attribute(touched, data, 'supplemental', {}),
            **get_attribute(touched, data, 'parameters', {})
        )

        # Construct seasons
        if 'seasons' in data:
            show.seasons = dict([
                (k, ModelRegistry['Season'].from_dict(collection, v, key=k, parent=show))
                for k, v in get_attribute(touched, data, 'seasons').items()
            ])

        # Ensure all attributes were touched
        omitted = [
            k for k in (set(data.keys()) - touched)
            if not k.startswith('_')
        ]

        if omitted:
            log.warn('Show.from_dict() omitted %d attribute(s): %s', len(omitted), ', '.join(omitted))

        return show

    def __repr__(self):
        if self.identifiers and self.names:
            service = self.identifiers.keys()[0]

            return '<Show %s: %r, names: %r>' % (
                service,
                self.identifiers[service],
                self.names
            )

        if self.identifiers:
            service = self.identifiers.keys()[0]

            return '<Show %s: %r>' % (
                service,
                self.identifiers[service]
            )

        if self.names:
            return '<Show names: %r>' % (
                self.names
            )

        return '<Show>'
