class Handler(object):
    __event__ = None

    __src__ = []
    __dst__ = []

    @classmethod
    def process(cls, obj, payload):
        pass


class SessionHandler(Handler):
    @staticmethod
    def has_media_changed(session, payload):
        if not session or not session.rating_key:
            return False

        return session.rating_key != payload.get('rating_key')
