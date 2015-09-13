from plugin.sync.handlers.core import MediaHandler


class CollectionHandler(MediaHandler):
    @staticmethod
    def get_operands(p_item, t_item):
        # Retrieve plex `added_at` from item
        if p_item is not None:
            p_added_at = p_item.get('added_at')
        else:
            p_added_at = None

        # Retrieve trakt `added_at` from item
        if type(t_item) is dict:
            t_added_at = t_item.get('collected_at')
        else:
            t_added_at = t_item.collected_at if t_item else None

        return p_added_at, t_added_at
