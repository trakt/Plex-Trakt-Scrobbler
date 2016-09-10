from trakt.objects.core.helpers import update_attributes


class Person(object):
    def __init__(self, client, keys=None, index=None):
        self._client = client

        self.keys = keys
        """
        :type: :class:`~python:list` of :class:`~python:tuple`

        Keys (for imdb, tvdb, etc..), defined as:

        ..code-block::

            [
                (<service>, <id>)
            ]

        """

        self.index = index
        """
        :type: :class:`~python:int`

        Playlist item index
        """

        self.name = None
        """
        :type: :class:`~python:str`

        Name
        """

    @property
    def pk(self):
        """Primary Key (unique identifier for the item)

        Provides the following identifiers (by media type):
         - **movie:** imdb
         - **show:** tvdb
         - **season:** tvdb
         - **episode:** tvdb
         - **custom_list:** trakt
         - **person:** tmdb

        :return: :code:`(<service>, <value>)` or :code:`None` if no primary key is available
        :rtype: :class:`~python:tuple`
        """
        if not self.keys:
            return None

        return self.keys[0]

    def _update(self, info=None, **kwargs):
        if not info:
            return

        update_attributes(self, info, [
            'name'
        ])

    @classmethod
    def _construct(cls, client, keys, info=None, index=None, **kwargs):
        person = cls(client, keys, index=index)
        person._update(info, **kwargs)

        return person

    def __getstate__(self):
        state = self.__dict__

        if hasattr(self, '_client'):
            del state['_client']

        return state

    def __repr__(self):
        if self.name:
            return '<Person %r>' % self.name

        return '<Person>'

    def __str__(self):
        return self.__repr__()
