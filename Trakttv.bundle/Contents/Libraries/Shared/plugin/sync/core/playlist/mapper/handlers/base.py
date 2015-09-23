class PlaylistHandler(object):
    def __init__(self, task):
        self.task = task

        self.table = None

    #
    # Table proxies
    #

    def get(self, *key):
        if self.table is None:
            return None

        return self.path_get(self.table, key, default=None)

    #
    # Class functions
    #

    def load(self, playlist, items=None):
        raise NotImplementedError

    #
    # Helpers
    #
    # TODO move methods to helper module
    #

    @staticmethod
    def path_get(d, keys, default=None):
        if type(keys) is not list:
            keys = list(keys)

        for key in keys[:-1]:
            if key not in d:
                return default

            d = d[key]

            if type(d) is not dict:
                break

        if type(d) is not dict:
            return d

        return d.get(keys[-1], default)

    @staticmethod
    def path_set(d, keys, value):
        for key in keys[:-1]:
            if key not in d:
                d[key] = {}

            d = d[key]

            if type(d) is not dict:
                break

        if type(d) is not dict:
            return False

        d[keys[-1]] = value
        return True
