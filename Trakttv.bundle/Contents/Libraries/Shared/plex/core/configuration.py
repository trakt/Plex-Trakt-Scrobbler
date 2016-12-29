from plex.core.context_collection import ContextCollection


class ConfigurationManager(object):
    def __init__(self):
        self.defaults = Configuration(self)
        self.stack = ContextCollection([self.defaults])

    @property
    def current(self):
        return self.stack[-1]

    def authentication(self, token=None):
        return Configuration(self).authentication(token)

    def cache(self, **definitions):
        return Configuration(self).cache(**definitions)

    def client(self, identifier=None, product=None, version=None):
        return Configuration(self).client(identifier, product, version)

    def device(self, name=None, system=None):
        return Configuration(self).device(name, system)

    def headers(self, headers=None):
        return Configuration(self).headers(headers)

    def platform(self, name=None, version=None):
        return Configuration(self).platform(name, version)

    def server(self, host='127.0.0.1', port=32400):
        return Configuration(self).server(host, port)

    def get(self, key, default=None):
        for x in range(len(self.stack) - 1, -1, -1):
            value = self.stack[x].get(key)

            if value is not None:
                return value

        return default

    def __getitem__(self, key):
        return self.get(key)

    def __setitem__(self, key, value):
        self.current[key] = value


class Configuration(object):
    def __init__(self, manager):
        self.manager = manager

        self.data = {}

    def authentication(self, token):
        self.data['authentication.token'] = token

        return self

    def cache(self, **definitions):
        for key, value in definitions.items():
            self.data['cache.%s' % key] = value

        return self

    def client(self, identifier, product, version):
        self.data['client.identifier'] = identifier

        self.data['client.product'] = product
        self.data['client.version'] = version

        return self

    def device(self, name, system):
        self.data['device.name'] = name
        self.data['device.system'] = system

        return self

    def headers(self, headers):
        self.data['headers'] = headers

        return self

    def platform(self, name, version):
        self.data['platform.name'] = name
        self.data['platform.version'] = version

        return self

    def server(self, host='127.0.0.1', port=32400):
        self.data['server.host'] = host
        self.data['server.port'] = port

        return self

    def get(self, key, default=None):
        return self.data.get(key, default)

    def __enter__(self):
        self.manager.stack.append(self)

    def __exit__(self, exc_type, exc_val, exc_tb):
        item = self.manager.stack.pop()

        assert item == self, 'Removed %r from stack, expecting %r' % (item, self)

        # Clear old context lists
        if len(self.manager.stack) == 1:
            self.manager.stack.clear()

    def __getitem__(self, key):
        return self.data[key]

    def __setitem__(self, key, value):
        self.data[key] = value
