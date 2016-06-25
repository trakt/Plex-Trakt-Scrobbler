from oem_framework.core.helpers import get_attribute
from oem_framework.models.core import BaseMapping, BaseMedia, ModelRegistry
from oem_framework.models.range import Range

import logging

log = logging.getLogger(__name__)


class Episode(BaseMedia):
    __slots__ = ['parent', 'season', 'number', 'names', 'mappings']
    __attributes__ = ['season', 'number', 'names', 'mappings']

    def __init__(self, collection, parent, number, identifiers=None, names=None, mappings=None, **parameters):
        super(Episode, self).__init__(collection, 'episode', identifiers, **parameters)
        self.parent = parent

        self.season = parent.number
        self.number = number

        self.names = self._parse_names(collection, identifiers, names) or {}

        self.mappings = mappings or []

    def to_dict(self, key=None, flatten=True):
        result = super(Episode, self).to_dict(key=key, flatten=flatten)

        if not flatten:
            return result

        # Flatten "names" attribute
        self._flatten_names(self.collection, result)

        # Remove "season" attribute if it matches the parent season
        if result.get('season') == self.parent.number:
            del result['season']

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

        # Construct movie
        episode = cls(
            collection,
            parent,
            key or number,

            identifiers=get_attribute(touched, data, 'identifiers'),
            names=names,

            supplemental=get_attribute(touched, data, 'supplemental', {}),
            **get_attribute(touched, data, 'parameters', {})
        )

        # Construct mappings
        if 'mappings' in data:
            episode.mappings = [
                ModelRegistry['EpisodeMapping'].from_dict(collection, v, parent=episode)
                for v in get_attribute(touched, data, 'mappings')
            ]

        # Ensure all attributes were touched
        omitted = [
            k for k in (set(data.keys()) - touched)
            if not k.startswith('_')
        ]

        if omitted:
            log.warn('Episode.from_dict() omitted %d attribute(s): %s', len(omitted), ', '.join(omitted))

        return episode

    def __repr__(self):
        if self.identifiers and self.names:
            service = list(self.identifiers.keys())[0]

            return '<Episode %s: %r, names: %r>' % (
                service,
                self.identifiers[service],
                self.names
            )

        if self.identifiers:
            service = list(self.identifiers.keys())[0]

            return '<Episode %s: %r>' % (
                service,
                self.identifiers[service]
            )

        if self.names:
            return '<Episode names: %r>' % (
                self.names
            )

        return '<Episode>'


class EpisodeMapping(BaseMapping):
    __slots__ = ['parent', 'season', 'number', 'timeline']

    def __init__(self, collection, parent, season, number, timeline=None):
        super(EpisodeMapping, self).__init__(collection)
        self.parent = parent

        self.season = season
        self.number = number

        self.timeline = timeline or {}

    @classmethod
    def from_dict(cls, collection, data, parent=None, **kwargs):
        if parent is None:
            raise ValueError('Missing required parameter: "parent"')

        touched = set()

        # Construct episode mapping
        episode_mapping = cls(
            collection,
            parent,

            # Identifier
            season=get_attribute(touched, data, 'season', parent.season),
            number=get_attribute(touched, data, 'number', parent.number)
        )

        # Parse "timeline" attribute
        if 'timeline' in data:
            episode_mapping.timeline = dict([
                (k, Range.from_dict(collection, v))
                for k, v in get_attribute(touched, data, 'timeline', {}).items()
            ])

        # Ensure all attributes were touched
        omitted = [
            k for k in (set(data.keys()) - touched)
            if not k.startswith('_')
        ]

        if omitted:
            log.warn('EpisodeMapping.from_dict() omitted %d attribute(s): %s', len(omitted), ', '.join(omitted))

        return episode_mapping

    def to_dict(self, key=None, flatten=True):
        result = {}

        # Identifier
        if self.season != self.parent.season:
            result['season'] = self.season

        if len(result) < 1 or self.number != self.parent.number:
            result['number'] = self.number

        # Range
        if self.timeline:
            def iterator():
                for k, v in self.timeline.items():
                    v = v.to_dict()

                    if not v:
                        continue

                    yield k, v

            timeline = dict(iterator())

            if timeline:
                result['timeline'] = timeline

        return result
