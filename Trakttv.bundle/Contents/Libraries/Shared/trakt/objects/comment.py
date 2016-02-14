from trakt.core.helpers import from_iso8601
from trakt.objects.core.helpers import update_attributes


class Comment(object):
    def __init__(self, client, keys):
        self._client = client

        self.keys = keys

        # Class attributes
        self.parent_id = None

        self.comment = None

        self.spoiler = None
        self.review = None

        self.replies = None
        self.likes = None

        self.created_at = None
        self.liked_at = None

        self.user = None
        self.user_rating = None

    @property
    def id(self):
        if self.pk is None:
            return None

        _, sid = self.pk

        return sid

    @property
    def pk(self):
        if not self.keys:
            return None

        return self.keys[0]

    def _update(self, info=None):
        if not info:
            return

        if 'created_at' in info:
            self.created_at = from_iso8601(info.get('created_at'))

        if 'liked_at' in info:
            self.liked_at = from_iso8601(info.get('liked_at'))

        update_attributes(self, info, [
            'parent_id',

            'comment',

            'spoiler',
            'review',

            'replies',
            'likes',

            'user',
            'user_rating'
        ])

    @classmethod
    def _construct(cls, client, keys, info, **kwargs):
        if not info:
            return None

        c = cls(client, keys, **kwargs)
        c._update(info)
        return c

    def __repr__(self):
        return '<Comment %r (%s)>' % (self.comment, self.id)

    def __str__(self):
        return self.__repr__()
