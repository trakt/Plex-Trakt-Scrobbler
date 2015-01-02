from trakt.interfaces.base import Interface

import inspect
import os

ROOT_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
INTERFACES_PATH = os.path.dirname(__file__)
SELF_PATH, _ = os.path.splitext(__file__)

UNC_PREFIX = '\\\\?\\'


def discover():
    for directory, _, files in os.walk(INTERFACES_PATH):
        for filename in files:
            if filename.startswith('base.'):
                continue

            if not filename.endswith('.py'):
                continue

            path = os.path.join(directory, filename)

            # Remove UNC prefix (if it exists)
            if path.startswith(UNC_PREFIX):
                path = path[len(UNC_PREFIX):]

            # Ignore current file
            if path.startswith(SELF_PATH):
                continue

            yield path


def load():
    paths = discover()

    def sort_key(path):
        fragments = len(path.split('/'))

        if path.endswith('__init__.py'):
            return fragments - 1

        return fragments

    paths = sorted(paths, key=sort_key)

    for path in paths:
        path = os.path.realpath(path)

        name, _ = os.path.splitext(os.path.relpath(path, ROOT_PATH))
        name = name.replace('\\', '.')

        mod = __import__(name, fromlist=['*'])

        for key, value in mod.__dict__.items():
            if key.startswith('_'):
                continue

            if not inspect.isclass(value):
                continue

            if not issubclass(value, Interface):
                continue

            if mod.__name__ != value.__module__:
                continue

            yield value


INTERFACES = list(load())


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
