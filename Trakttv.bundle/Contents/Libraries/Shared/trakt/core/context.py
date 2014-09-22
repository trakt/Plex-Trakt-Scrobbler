import inspect


class Context(object):
    def __init__(self, client, access_token=None):
        self.client = client

        self._access_token = access_token

    @property
    def access_token(self):
        if self._access_token is not None:
            return self._access_token

        return self.client.access_token

    def __enter__(self):
        self.client._context_stack.append(self)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        ctx = self.client._context_stack.pop()

        assert ctx is self, 'Popped wrong context. (%r instead of %r)' % (ctx, self)
