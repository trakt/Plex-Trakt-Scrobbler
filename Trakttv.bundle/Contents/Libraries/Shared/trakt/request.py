from trakt.helpers import setdefault

from requests import Request
import json


class TraktRequest(object):
    def __init__(self, client, **kwargs):
        self.client = client
        self.kwargs = kwargs

        self.request = None

        # Parsed Attributes
        self.path = None
        self.params = None

        self.data = None
        self.method = None

    def prepare(self):
        self.request = Request()

        self.transform_parameters()
        self.request.url = self.construct_url()

        self.request.data = json.dumps(self.transform_data())
        self.request.method = self.transform_method()

        return self.request.prepare()

    def transform_parameters(self):
        # Transform `path`
        self.path = self.kwargs.get('path')

        if not self.path.startswith('/'):
            self.path = '/' + self.path

        if self.path.endswith('/'):
            self.path = self.path[:-1]

        # Transform `params` into list
        self.params = self.kwargs.get('params') or []

        if isinstance(self.params, basestring):
            self.params = [self.params]

    def transform_method(self):
        self.method = self.kwargs.get('method')

        # Pick `method` (if not provided)
        if not self.method:
            self.method = 'POST' if self.data else 'GET'

        return self.method

    def transform_data(self):
        self.data = self.kwargs.get('data') or {}

        # Set credentials (if not provided)
        if self.kwargs.get('credentials'):
            setdefault(self.data, self.kwargs['credentials'])

        return self.data

    def construct_url(self):
        """Construct a full trakt request URI, with `api_key` and `params`."""
        path = [self.path, self.client.api_key]
        path.extend(self.params)

        return self.client.base_url + '/'.join(x for x in path if x)
