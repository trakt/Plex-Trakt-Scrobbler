from oem_format_minimize.core.minimize import Minimize
from oem_format_minimize.protocol import *
from oem_framework.models import *
from oem_framework.format import Format

import inspect

# Setup model protocols
Index.set_protocol('minimize', IndexMinimizeProtocol)
Metadata.set_protocol('minimize', MetadataMinimizeProtocol)

Movie.set_protocol('minimize', MovieMinimizeProtocol)
Show.set_protocol('minimize', ShowMinimizeProtocol)
Season.set_protocol('minimize', SeasonMinimizeProtocol)
Episode.set_protocol('minimize', EpisodeMinimizeProtocol)


class MinimalFormat(Format):
    def encode(self, model, data, **kwargs):
        # Retrieve item minimize protocol
        protocol = model.__protocols__.get('minimize') if model.__protocols__ else None

        if protocol is None:
            raise ValueError('Model %r has no "minimize" protocol defined' % model)

        if inspect.isfunction(protocol):
            protocol = protocol()

        return Minimize.encode(data, protocol)

    def decode(self, model, encoded, children=True, ignore_keys=None, **kwargs):
        if model.__wrapper__:
            media = kwargs.get('media')

            if media is None:
                raise ValueError('Missing required parameters: "media"')

            model = model.resolve(media)

        # Retrieve item minimize protocol
        protocol = model.__protocols__.get('minimize') if model.__protocols__ else None

        if protocol is None:
            raise ValueError('Model %r has no "minimize" protocol defined' % model)

        if inspect.isfunction(protocol):
            protocol = protocol()

        return Minimize.decode(
            encoded, protocol,
            children=children,
            ignore_keys=ignore_keys
        )

    def from_dict(self, collection, model, encoded, children=True, **kwargs):
        # Decode dictionary with minimized data protocol
        data = self.decode(model, encoded, children=children, **kwargs)

        # Parse `model` from `data`
        return Format.from_dict(self, collection, model, data, **kwargs)

    def to_dict(self, item, **kwargs):
        # Convert `item` to `data` dictionary
        data = Format.to_dict(self, item, **kwargs)

        # Encode dictionary with minimized data protocol
        return self.encode(item.__class__, data)
