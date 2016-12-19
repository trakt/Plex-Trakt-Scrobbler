from plugin.scrobbler.core import SessionEngine, SessionHandler


@SessionEngine.register
class PausedHandler(SessionHandler):
    __event__ = 'paused'

    __src__ = ['pause', 'start', 'stop']
    __dst__ = ['pause', 'stop']

    @classmethod
    def process(cls, session, payload):
        # Handle media change
        if cls.has_media_changed(session, payload) and session.state in ['start', 'pause']:
            yield 'stop', session.payload

        # Handle current media
        if cls.should_scrobble(session, payload):
            if session.state in ['start', 'pause']:
                yield 'stop', payload
        elif session.state == 'start':
            yield 'pause', payload
        elif session.state == 'pause':
            yield None, payload
