from oem_framework.core.helpers import get_attribute
from oem_framework.models.core import BaseMapping, BaseMedia, ModelRegistry

import logging
import six

log = logging.getLogger(__name__)


class Season(BaseMedia):
    __slots__ = ['parent', 'number', 'names', 'mappings', 'episodes']
    __attributes__ = ['number', 'names', 'mappings', 'episodes']

    def __init__(self, collection, parent, number, identifiers=None, names=None, mappings=None, episodes=None, **parameters):
        super(Season, self).__init__(collection, 'season', identifiers, **parameters)
        self.parent = parent

        self.number = number

        self.names = self._parse_names(collection, identifiers, names) or {}

        self.mappings = mappings or []
        self.episodes = episodes or {}

    def to_dict(self, key=None, flatten=True):
        result = super(Season, self).to_dict(key=key, flatten=flatten)

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

        # Parse "names" attribute
        names = get_attribute(touched, data, 'names', [])

        if type(names) is list:
            names = set(names)

        # Construct season
        season = cls(
            collection,
            parent,
            key,

            identifiers=get_attribute(touched, data, 'identifiers'),
            names=names,

            supplemental=get_attribute(touched, data, 'supplemental', {}),
            **get_attribute(touched, data, 'parameters', {})
        )

        # Construct episodes
        if 'episodes' in data:
            def parse_episodes():
                for k, v in get_attribute(touched, data, 'episodes').items():
                    if type(v) is list:
                        yield k, [
                            ModelRegistry['Episode'].from_dict(collection, v_episode, key=k, parent=season)
                            for v_episode in v
                        ]
                    else:
                        yield k, ModelRegistry['Episode'].from_dict(collection, v, key=k, parent=season)

            season.episodes = dict(parse_episodes())

        # Construct mappings
        if 'mappings' in data:
            season.mappings = [
                ModelRegistry['SeasonMapping'].from_dict(collection, v, parent=season)
                for v in get_attribute(touched, data, 'mappings')
            ]

        # Ensure all attributes were touched
        omitted = [
            k for k in (set(data.keys()) - touched)
            if not k.startswith('_')
        ]

        if omitted:
            log.warn('Season.from_dict() omitted %d attribute(s): %s', len(omitted), ', '.join(omitted))

        return season

    def __repr__(self):
        if self.identifiers and self.names:
            service = list(self.identifiers.keys())[0]

            return '<Season %s: %r, names: %r>' % (
                service,
                self.identifiers[service],
                self.names
            )

        if self.identifiers:
            service = list(self.identifiers.keys())[0]

            return '<Season %s: %r>' % (
                service,
                self.identifiers[service]
            )

        if self.names:
            return '<Season names: %r>' % (
                self.names,
            )

        return '<Season>'


class SeasonMapping(BaseMapping):
    __slots__ = ['identifiers', 'names', 'season', 'start', 'end', 'offset']

    def __init__(self, collection, season, start, end, offset, identifiers=None, names=None):
        super(SeasonMapping, self).__init__(collection)

        self.identifiers = identifiers or {}
        self.names = self._parse_names(collection, identifiers, names) or {}

        self.season = season

        self.start = start
        self.end = end
        self.offset = offset

    def to_dict(self, key=None, flatten=True):
        result = {
            'season': self.season,

            'start': self.start,
            'end': self.end,

            'offset': self.offset
        }

        if self.identifiers:
            result['identifiers'] = self.identifiers

        if self.names:
            if type(self.names) is set:
                result['names'] = list(self.names)
            elif type(self.names) is dict:
                result['names'] = {}

                for key, value in six.iteritems(self.names):
                    if type(value) is set:
                        value = list(value)

                    result['names'][key] = value
            else:
                result['names'] = self.names

        if not flatten:
            return result

        # Flatten "names" attribute
        self._flatten_names(self.collection, result)

        return result

    @classmethod
    def from_dict(cls, collection, data, **kwargs):
        touched = set()

        # Construct episode mapping
        season_mapping = cls(
            collection,

            identifiers=get_attribute(touched, data, 'identifiers'),
            names=set(get_attribute(touched, data, 'names', [])),

            season=get_attribute(touched, data, 'season'),

            start=get_attribute(touched, data, 'start'),
            end=get_attribute(touched, data, 'end'),
            offset=get_attribute(touched, data, 'offset')
        )

        # Ensure all attributes were touched
        omitted = [
            k for k in (set(data.keys()) - touched)
            if not k.startswith('_')
        ]

        if omitted:
            log.warn('SeasonMapping.from_dict() omitted %d attribute(s): %s', len(omitted), ', '.join(omitted))

        return season_mapping
