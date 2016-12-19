from plugin.scrobbler.core import SessionEngine, SessionHandler


@SessionEngine.register
class PlayingHandler(SessionHandler):
    __event__ = 'playing'

    __src__ = ['create', 'pause', 'stop', 'start']
    __dst__ = ['start', 'stop']

    @classmethod
    def process(cls, session, payload):
        # Handle media change
        if cls.has_media_changed(session, payload) and session.state in ['start', 'pause']:
            yield 'stop', session.payload

        # Handle current media
        if cls.has_finished(session, payload):
            if session.state in ['start', 'pause']:
                yield 'stop', payload
        elif session.state in ['create', 'pause', 'stop']:
            yield 'start', payload
        elif session.state == 'start':
            yield None, payload
