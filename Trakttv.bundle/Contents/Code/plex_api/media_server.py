class PlexMediaServer(object):
    base_url = 'http://localhost:32400'

    @classmethod
    def request(cls, path):
        if not path.startswith('/'):
            path = '/' + path

        return XML.ElementFromURL(cls.base_url + path, errors='ignore')
