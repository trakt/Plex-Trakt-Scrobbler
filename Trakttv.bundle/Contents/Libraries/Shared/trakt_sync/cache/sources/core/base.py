class Source(object):
    def __init__(self, main):
        self.main = main

    @property
    def data(self):
        return self.main.data

    @property
    def media(self):
        return self.main.media

    def get_collection(self, username, *args):
        return self.main._get_collection(username, *args)

    def get_store(self, username, *args):
        return self.main._get_store(username, *args)

    def invalidate(self, username, *args):
        raise NotImplementedError

    def refresh(self, username):
        raise NotImplementedError

    def update_store(self, key, current):
        collection = self.get_collection(*key)
        collection_keys = set(collection['store'].keys())

        # Add + Update items
        collection['store'].update(current)

        # Delete items
        collection['store'].delete(collection_keys - set(current.keys()))
