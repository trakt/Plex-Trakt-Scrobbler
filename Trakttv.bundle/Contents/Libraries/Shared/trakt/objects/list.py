from trakt.core.helpers import from_iso8601
from trakt.objects.core.helpers import update_attributes


class List(object):
    def __init__(self, client, keys):
        self._client = client

        self.keys = keys

        # Class attributes
        self.name = None
        self.description = None
        self.likes = None

        self.allow_comments = None
        self.display_numbers = None

        self.liked_at = None
        self.updated_at = None

        self.comment_count = None
        self.item_count = None

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

        if 'liked_at' in info:
            self.liked_at = from_iso8601(info.get('liked_at'))

        if 'updated_at' in info:
            self.updated_at = from_iso8601(info.get('updated_at'))

        update_attributes(self, info, [
            'name',
            'description',
            'likes',

            'allow_comments',
            'display_numbers',

            'comment_count',
            'item_count'
        ])

    def __getstate__(self):
        state = self.__dict__

        if hasattr(self, '_client'):
            del state['_client']

        return state

    def __repr__(self):
        _, sid = self.pk

        return '<List %r (%s)>' % (self.name, sid)

    def __str__(self):
        return self.__repr__()


class CustomList(List):
    def __init__(self, client, keys, username=None):
        super(CustomList, self).__init__(client, keys)

        self.username = username

        self.privacy = None

    def _update(self, info=None):
        if not info:
            return

        super(CustomList, self)._update(info)

        update_attributes(self, info, [
            'privacy'
        ])

        # Update with user details
        user = info.get('user', {})

        if user.get('username'):
            self.username = user['username']

    @classmethod
    def _construct(cls, client, keys, info, **kwargs):
        if not info:
            return None

        l = cls(client, keys, **kwargs)
        l._update(info)
        return l

    def items(self, **kwargs):
        return self._client['users/*/lists/*'].items(self.username, self.id, **kwargs)

    #
    # Owner actions
    #

    def add(self, items, **kwargs):
        return self._client['users/*/lists/*'].add(self.username, self.id, items, **kwargs)

    def delete(self, **kwargs):
        return self._client['users/*/lists/*'].delete(self.username, self.id, **kwargs)

    def update(self, **kwargs):
        item = self._client['users/*/lists/*'].update(self.username, self.id, return_type='data', **kwargs)

        if not item:
            return False

        self._update(item)
        return True

    def remove(self, items, **kwargs):
        return self._client['users/*/lists/*'].remove(self.username, self.id, items, **kwargs)

    #
    # Actions
    #

    def like(self, **kwargs):
        return self._client['users/*/lists/*'].like(self.username, self.id, **kwargs)

    def unlike(self, **kwargs):
        return self._client['users/*/lists/*'].unlike(self.username, self.id, **kwargs)
