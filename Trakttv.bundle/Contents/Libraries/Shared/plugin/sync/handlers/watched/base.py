from plugin.sync.handlers.core import MediaHandler


class WatchedHandler(MediaHandler):
    @staticmethod
    def get_operands(p_item, t_item):
        p_viewed_at = p_item.get('settings', {}).get('last_viewed_at')

        # Retrieve trakt `viewed_at` from item
        if type(t_item) is dict:
            t_viewed_at = t_item.get('last_watched_at')
        else:
            t_viewed_at = t_item.last_watched_at if t_item else None

        return p_viewed_at, t_viewed_at
