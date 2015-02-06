from trakt.core.context_collection import ContextCollection

DEFAULT_HTTP_RETRY = False
DEFAULT_HTTP_MAX_RETRIES = 3
DEFAULT_HTTP_RETRY_SLEEP = 5
DEFAULT_HTTP_TIMEOUT = (6.05, 24)


class ConfigurationManager(object):
    def __init__(self):
        self.defaults = Configuration(self)
        self.stack = ContextCollection([self.defaults])

    @property
    def current(self):
        return self.stack[-1]

    def app(self, name=None, version=None, date=None):
        return Configuration(self).app(name, version, date)

    def auth(self, login=None, token=None):
        return Configuration(self).auth(login, token)

    def client(self, id=None, secret=None):
        return Configuration(self).client(id, secret)

    def http(self, retry=DEFAULT_HTTP_RETRY, max_retries=DEFAULT_HTTP_MAX_RETRIES, retry_sleep=DEFAULT_HTTP_RETRY_SLEEP,
             timeout=DEFAULT_HTTP_TIMEOUT):

        return Configuration(self).http(retry, max_retries, retry_sleep, timeout)

    def oauth(self, token=None):
        return Configuration(self).oauth(token)

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

    def app(self, name=None, version=None, date=None):
        self.data['app.name'] = name
        self.data['app.version'] = version
        self.data['app.date'] = date

        return self

    def auth(self, login=None, token=None):
        self.data['auth.login'] = login
        self.data['auth.token'] = token

        return self

    def client(self, id=None, secret=None):
        self.data['client.id'] = id
        self.data['client.secret'] = secret

        return self

    def http(self, retry=DEFAULT_HTTP_RETRY, max_retries=DEFAULT_HTTP_MAX_RETRIES, retry_sleep=DEFAULT_HTTP_RETRY_SLEEP,
             timeout=DEFAULT_HTTP_TIMEOUT):

        self.data['http.retry'] = retry
        self.data['http.max_retries'] = max_retries
        self.data['http.retry_sleep'] = retry_sleep

        self.data['http.timeout'] = timeout

        return self

    def oauth(self, token=None):
        self.data['oauth.token'] = token

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
