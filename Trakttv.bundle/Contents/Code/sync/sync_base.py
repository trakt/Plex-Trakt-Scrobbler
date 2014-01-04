# from core.trakt import Trakt
# from plex.media_server_new import PlexMediaServer


class SyncBase(object):
    title = "Unknown"
    children = []

    def __init__(self):
        # Activate children and create dictionary map
        self.children = [x() for x in self.children]

    def run(self):
        # Run sub functions (starting with 'run_')
        sub_functions = [(x, getattr(self, x)) for x in dir(self) if x.startswith('run_')]

        for name, func in sub_functions:
            Log.Debug('Running sub-function in task %s with name "%s"' % (self, name))
            func()

        # Run child tasks
        for child in self.children:
            Log.Debug('Running child task %s' % child)
            child.run()

    @staticmethod
    def update_progress(current, start=0, end=100):
        raise ReferenceError()

    @staticmethod
    def is_stopping():
        raise ReferenceError()

    #
    # Trakt
    #

    # # TODO per-sync cached results
    # @classmethod
    # def get_trakt_library(cls, media, marked):
    #     return Trakt.User.get_library(media, marked)
    #
    # # TODO per-sync cached results
    # @classmethod
    # def get_trakt_ratings(cls, media):
    #     return Trakt.User.get_ratings(media)

    #
    # Plex Media Server
    #

    # # TODO per-sync cached results
    # @classmethod
    # def get_plex_sections(cls, types=None, keys=None):
    #     return PlexMediaServer.get_sections(types, keys)
    #
    #
    # # TODO per-sync cached results
    # @classmethod
    # def get_plex_library(cls, types=None, keys=None):
    #     return PlexMediaServer.get_library(types, keys)
