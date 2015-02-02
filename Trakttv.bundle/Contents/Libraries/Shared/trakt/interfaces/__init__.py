from trakt.interfaces.base import Interface

from trakt.interfaces.auth import *
from trakt.interfaces.oauth import *
from trakt.interfaces.scrobble import *
from trakt.interfaces.sync import *

INTERFACES = [
    # /
    AuthInterface,
    OAuthInterface,

    ScrobbleInterface,

    # /sync/
    SyncInterface,
    SyncCollectionInterface,
    SyncHistoryInterface,
    SyncRatingsInterface,
    SyncWatchedInterface,
    SyncWatchlistInterface
]


def get_interfaces():
    for interface in INTERFACES:
        if not interface.path:
            continue

        path = interface.path.strip('/')

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
        if len(path) == 0:
            continue

        key = path.pop(0)

        if len(path) == 0:
            d[key] = interface(client)
            continue

        value = d.get(key, {})

        if type(value) is not dict:
            value = {None: value}

        construct_map(client, value, [(path, interface)])

        d[key] = value

    return d
