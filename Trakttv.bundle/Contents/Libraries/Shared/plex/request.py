from requests import Request
import json
import urllib


class PlexRequest(object):
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

        self.request.data = self.transform_data()
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

        if type(self.params) is not list:
            self.params = [self.params]

    def transform_method(self):
        self.method = self.kwargs.get('method')

        # Pick `method` (if not provided)
        if not self.method:
            self.method = 'POST' if self.data else 'GET'

        return self.method

    def transform_data(self):
        self.data = self.kwargs.get('data')

        if self.data is None:
            return None

        return json.dumps(self.data)

    def construct_url(self):
        """Construct a full plex request URI, with `params`."""
        path = [self.path]
        path.extend([str(x) for x in self.params])

        url = self.client.base_url + '/'.join(x for x in path if x)
        query = self.kwargs.get('query')

        if query:
            url += '?' + urllib.urlencode(query)

        return url
