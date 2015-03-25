from plugin.scrobbler.core import SessionEngine, SessionHandler


@SessionEngine.register
class PlayingHandler(SessionHandler):
    __event__ = 'playing'

    __src__ = ['create', 'pause', 'stop']
    __dst__ = ['start', 'stop']

    @classmethod
    def process(cls, session, payload):
        if cls.has_media_changed(session, payload):
            yield 'stop', session.payload
        elif cls.has_finished(session, payload):
            yield 'stop', payload
            return
        elif session.state == 'start':
            # Duplicate action, just update the current data
            yield None, payload
            return

        # Create new 'start' event
        yield 'start', payload
