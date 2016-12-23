class Handler(object):
    __event__ = None

    __src__ = []
    __dst__ = []

    @classmethod
    def is_valid_source(cls, state):
        return state in cls.__src__

    @classmethod
    def is_valid_destination(cls, state):
        return state in cls.__dst__

    @classmethod
    def process(cls, obj, payload):
        pass


class SessionHandler(Handler):
    @staticmethod
    def has_finished(session, payload):
        if not session or not session.duration:
            return False

        # Calculate session progress
        # TODO update to support multi-part sessions
        progress = float(payload.get('view_offset')) / session.duration

        # Session is finished when `progress` reaches at least 100%
        return progress >= 1.0

    @staticmethod
    def has_media_changed(session, payload):
        if not session or not session.rating_key:
            return False

        if session.rating_key != payload.get('rating_key'):
            return True

        if session.part != payload.get('part', 1):
            return True

        return False

    @staticmethod
    def should_scrobble(session, payload):
        if not session or not session.duration:
            return False

        # Calculate session progress
        # TODO update to support multi-part sessions
        progress = float(payload.get('view_offset')) / session.duration

        # Session is finished when `progress` reaches at least 98%
        return progress >= 0.98
