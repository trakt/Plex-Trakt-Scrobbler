from plugin.sync.handlers.core import MediaHandler


class CollectionHandler(MediaHandler):
    @staticmethod
    def get_operands(p_item, t_item):
        p_added_at = p_item.get('added_at')

        # Retrieve trakt `viewed_at` from item
        if type(t_item) is dict:
            t_added_at = t_item.get('collected_at')
        else:
            t_added_at = t_item.collected_at if t_item else None

        return p_added_at, t_added_at
