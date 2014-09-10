from plex.interfaces.channel import ChannelInterface
from plex.interfaces.library import LibraryInterface
from plex.interfaces.library.metadata import LibraryMetadataInterface
from plex.interfaces.plugin import PluginInterface
from plex.interfaces.preferences import PreferencesInterface
from plex.interfaces.root import RootInterface
from plex.interfaces.section import SectionInterface
from plex.interfaces.status import StatusInterface


# TODO automatic interface discovery

INTERFACES = [
    RootInterface,

    # /
    ChannelInterface,
    LibraryInterface,
    StatusInterface,

    # /library
    LibraryMetadataInterface,
    SectionInterface,

    # /:
    PluginInterface,
    PreferencesInterface
]


def get_interfaces():
    for interface in INTERFACES:
        if interface.path:
            path = interface.path.strip('/')
        else:
            path = ''

        if path:
            path = path.split('/')
        else:
            path = []

        yield path, interface


def construct_map(client, d=None, interfaces=None):
    if d is None:
        d = {}

    if interfaces is None:
        interfaces = get_interfaces()

    for path, interface in interfaces:
        if len(path) > 0:
            key = path.pop(0)
        else:
            key = None

        if len(path) == 0:
            d[key] = interface(client)
            continue

        value = d.get(key, {})

        if type(value) is not dict:
            value = {None: value}

        construct_map(client, value, [(path, interface)])

        d[key] = value

    return d
