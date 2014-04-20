from trakt.interfaces.account import AccountInterface
from trakt.interfaces.movie import MovieInterface
from trakt.interfaces.rate import RateInterface
from trakt.interfaces.show import ShowInterface
from trakt.interfaces.show.episode import ShowEpisodeInterface
from trakt.interfaces.user import UserInterface
from trakt.interfaces.user.library import UserLibraryInterface
from trakt.interfaces.user.ratings import UserRatingsInterface


# TODO automatic interface discovery
INTERFACES = [
    # /
    AccountInterface,
    RateInterface,

    MovieInterface,
    ShowInterface,
    ShowEpisodeInterface,

    # /user
    UserInterface,
    UserLibraryInterface,
    UserRatingsInterface
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
