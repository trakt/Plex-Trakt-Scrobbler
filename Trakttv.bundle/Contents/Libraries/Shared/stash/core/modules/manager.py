from stash.lib import six
from stash.lib.six.moves.urllib import parse as urlparse

import inspect
import logging

log = logging.getLogger(__name__)


class ModuleManager(object):
    modules = {}

    @classmethod
    def construct(cls, stash, group, value):
        if isinstance(value, six.string_types):
            obj = cls.from_uri(group, value)
        elif inspect.isclass(value):
            obj = value()
        else:
            obj = value

        if obj is None:
            return None

        obj.stash = stash

        return obj

    @classmethod
    def from_uri(cls, group, uri):
        if group not in cls.modules:
            return None

        # Retrieve scheme from URI
        scheme = cls.get_scheme(uri)

        if not scheme:
            return None

        # Ensure scheme is registered
        cls.register_scheme(scheme)

        # Parse URI
        result = urlparse.urlparse(uri)
        key = result.scheme

        if key not in cls.modules[group]:
            return None

        module = cls.modules[group][key]

        # Parse `path`
        args = []

        path = result.path.lstrip('/')

        if path:
            args.append(result.path.lstrip('/'))

        # Parse `query`
        kwargs = dict(urlparse.parse_qsl(result.query))

        # Construct module
        return module(*args, **kwargs)

    @classmethod
    def get_scheme(cls, uri):
        pos = uri.find('://')

        if pos < 0:
            return None

        return uri[:pos]

    @classmethod
    def register(cls, module):
        group = module.__group__
        key = module.__key__

        if not group or not key:
            log.warn('Unable to register: %r - missing a "__group__" or "__key__" attribute', module)
            return

        if group not in cls.modules:
            cls.modules[group] = {}

        if key in cls.modules[group]:
            log.warn('Unable to register: %r - already registered', module)
            return

        cls.modules[group][key] = module

    @classmethod
    def register_scheme(cls, scheme):
        for method in filter(lambda s: s.startswith('uses_'), dir(urlparse)):
            schemes = getattr(urlparse, method)

            if scheme in schemes:
                continue

            schemes.append(scheme)
