from trakt.core.helpers import from_iso8601


class Rating(object):
    def __init__(self, client, value=None, timestamp=None):
        self._client = client

        self.value = value
        self.timestamp = timestamp

    @classmethod
    def _construct(cls, client, info):
        if not info or 'rating' not in info:
            return

        r = cls(client)
        r.value = info.get('rating')
        r.timestamp = from_iso8601(info.get('rated_at'))
        return r

    def __getstate__(self):
        state = self.__dict__

        if hasattr(self, '_client'):
            del state['_client']

        return state

    def __eq__(self, other):
        if not isinstance(other, Rating):
            return NotImplemented

        return self.value == other.value and self.timestamp == other.timestamp

    def __repr__(self):
        return '<Rating %s/10 (%s)>' % (self.value, self.timestamp)

    def __str__(self):
        return self.__repr__()
