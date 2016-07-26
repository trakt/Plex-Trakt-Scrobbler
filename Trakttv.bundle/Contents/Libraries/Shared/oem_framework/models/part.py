from oem_framework.core.helpers import get_attribute
from oem_framework.models.core import BaseMedia

import logging

log = logging.getLogger(__name__)


class Part(BaseMedia):
    __slots__ = ['parent', 'number', 'names']
    __attributes__ = ['number', 'names']

    def __init__(self, collection, parent, number, identifiers=None, names=None, **parameters):
        super(Part, self).__init__(collection, 'part', identifiers, **parameters)
        self.parent = parent

        self.number = number

        self.names = self._parse_names(collection, identifiers, names) or {}

    def to_dict(self, key=None, flatten=True):
        result = super(Part, self).to_dict(key=key, flatten=flatten)

        if not flatten:
            return result

        # Flatten "names" attribute
        self._flatten_names(self.collection, result)

        # Remove "number" attribute if it matches the parent dictionary key
        if len(result) > 0 and key is not None and result.get('number') == key:
            del result['number']

        return result

    @classmethod
    def from_dict(cls, collection, data, key=None, parent=None, **kwargs):
        if key is None:
            raise ValueError('Missing required parameter: "key"')

        if parent is None:
            raise ValueError('Missing required parameter: "parent"')

        touched = set()

        # Identifier
        number = get_attribute(touched, data, 'number')

        # Parse "names" attribute
        names = get_attribute(touched, data, 'names', [])

        if type(names) is list:
            names = set(names)

        # Construct part
        part = cls(
            collection,
            parent,
            key or number,

            identifiers=get_attribute(touched, data, 'identifiers'),
            names=names,

            supplemental=get_attribute(touched, data, 'supplemental', {}),
            **get_attribute(touched, data, 'parameters', {})
        )

        # Ensure all attributes were touched
        omitted = [
            k for k in (set(data.keys()) - touched)
            if not k.startswith('_')
        ]

        if omitted:
            log.warn('Part.from_dict() omitted %d attribute(s): %s', len(omitted), ', '.join(omitted))

        return part

    def __repr__(self):
        if self.identifiers and self.names:
            service = list(self.identifiers.keys())[0]

            return '<Part %s: %r, names: %r>' % (
                service,
                self.identifiers[service],
                self.names
            )

        if self.identifiers:
            service = list(self.identifiers.keys())[0]

            return '<Part %s: %r>' % (
                service,
                self.identifiers[service]
            )

        if self.names:
            return '<Part names: %r>' % (
                self.names
            )

        return '<Part>'