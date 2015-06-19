class Option(object):
    __database__ = None
    __plex__ = None

    def get(self):
        raise NotImplementedError

    def on_database_changed(self, value):
        raise NotImplementedError

    def on_plex_changed(self, value):
        raise NotImplementedError
