from plugin.scrobbler.core import SessionEngine, SessionHandler


@SessionEngine.register
class StoppedHandler(SessionHandler):
    __event__ = 'stopped'

    __src__ = ['pause', 'start']
    __dst__ = ['stop']

    @classmethod
    def process(cls, session, payload):
        if session.state == 'stop':
            # Duplicate action, just update the current data
            yield None, payload
            return

        yield 'stop', payload
