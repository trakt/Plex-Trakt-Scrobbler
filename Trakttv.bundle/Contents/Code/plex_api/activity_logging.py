from plex_api.activity import ActivityMethod, PlexActivity


class Logging(ActivityMethod):
    name = 'Logging'

    @classmethod
    def test(cls):
        Log.Info('%s method not available' % cls.name)
        return False

    def run(self):
        raise NotImplementedError()

PlexActivity.register(Logging)
