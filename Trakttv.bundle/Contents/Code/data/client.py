from core.helpers import build_repr
from core.model import DictModel


class Client(DictModel):
    def __init__(self, client_id=None, name=None, address=None):
        """
        :type client_id: str
        :type name: str
        """

        super(Client, self).__init__(client_id)

        self.name = name
        self.address = address

    @classmethod
    def from_section(cls, section):
        if section is None:
            return None

        return Client(
            section.get('machineIdentifier'),
            section.get('name'),
            section.get('address')
        )

    def __repr__(self):
        return build_repr(self, [
            'key', 'name', 'address'
        ])

    def __str__(self):
        return self.__repr__()
