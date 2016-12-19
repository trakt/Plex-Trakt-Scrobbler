from plugin.scrobbler.core import SessionEngine, SessionHandler


@SessionEngine.register
class StoppedHandler(SessionHandler):
    __event__ = 'stopped'

    __src__ = ['pause', 'start', 'stop']
    __dst__ = ['stop']

    @classmethod
    def process(cls, session, payload):
        # Handle media change
        if cls.has_media_changed(session, payload) and session.state in ['start', 'pause']:
            yield 'stop', session.payload

        # Handle current media
        if session.state in ['start', 'pause']:
            yield 'stop', payload
        elif session.state == 'stop':
            yield None, payload
