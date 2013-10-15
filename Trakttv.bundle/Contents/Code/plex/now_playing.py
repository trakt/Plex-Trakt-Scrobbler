from plex.media_server import PlexMediaServer


class NowPlayingMethods(object):
    class Base(object):
        name = None

        @classmethod
        def test(cls):
            return False

        def start(self):
            raise NotImplementedError()

    class WebSocket(Base):
        name = 'WebSocket'

        def __init__(self):
            pass

        @classmethod
        def test(cls):
            try:
                PlexMediaServer.request('status/sessions')
                return True
            except Ex.HTTPError:
                pass
            except Ex.URLError:
                pass

            Log.Info('%s method not available' % cls.name)
            return False

        def run(self):
            raise NotImplementedError()

    class Logging(Base):
        name = 'Logging'

        def __init__(self):
            pass

        @classmethod
        def test(cls):
            Log.Info('%s method not available' % cls.name)
            return False

        def run(self):
            raise NotImplementedError()


class PlexNowPlaying(object):
    available_methods = [
        NowPlayingMethods.WebSocket,
        NowPlayingMethods.Logging
    ]

    current_method = None

    @classmethod
    def test(cls):
        for m in cls.available_methods:
            if m.test():
                cls.current_method = m()
                Log.Info('Picked method %s' % cls.current_method.name)
                break

        if not cls.current_method:
            Log.Warn('No method available to determine now playing status, auto-scrobbling not available.')
            return False

        return True

    @classmethod
    def run(cls):
        if not cls.current_method:
            return

        cls.current_method.run()
