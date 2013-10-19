from data.dict_object import DictObject


class User(DictObject):
    def __init__(self, user_id=None, title=None):
        """
        :type user_id: str
        :type title: str
        """

        super(User, self).__init__(user_id)

        self.title = title
        self.user_id = user_id

    @staticmethod
    def from_section(section):
        """
        :type section: ?

        :rtype: User
        """

        if not section:
            Log.Debug("[User.from_section] Invalid section")
            return None

        elements = section.findall('User')
        if not len(elements):
            Log.Info('[User.from_section] Unable to find "User" element.')
            return None

        return User(
            elements[0].get('id'),
            elements[0].get('title')
        )
