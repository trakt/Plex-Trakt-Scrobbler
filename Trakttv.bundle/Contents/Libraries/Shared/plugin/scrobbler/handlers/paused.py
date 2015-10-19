from plugin.scrobbler.core import SessionEngine, SessionHandler


@SessionEngine.register
class PausedHandler(SessionHandler):
    __event__ = 'paused'

    __src__ = ['pause', 'start', 'stop']
    __dst__ = ['pause']

    @classmethod
    def process(cls, session, payload):
        if session.state in ['pause', 'stop']:
            # Ignore action, just update the current data
            yield None, payload
            return

        yield 'pause', payload
