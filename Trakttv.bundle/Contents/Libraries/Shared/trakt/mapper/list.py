from trakt.mapper.core.base import Mapper


class ListMapper(Mapper):
    @classmethod
    def custom_list(cls, client, item, **kwargs):
        i_list = item

        # Retrieve item keys
        pk, keys = cls.get_ids('custom_list', i_list)

        if pk is None:
            return None

        # Create object
        return cls.construct(client, 'custom_list', i_list, keys, **kwargs)
