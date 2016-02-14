from plugin.sync.handlers.core import MediaHandler


class WatchedHandler(MediaHandler):
    @staticmethod
    def get_operands(p_item, t_item):
        # Retrieve plex `viewed_at` from item
        if p_item is not None:
            p_settings = p_item.get('settings', {})
            p_view_count = p_settings.get('view_count', 0)

            if p_view_count > 0:
                # Item completely watched in plex
                p_viewed_at = p_settings.get('last_viewed_at')
            else:
                # Item partially watched in plex
                p_viewed_at = None
        else:
            p_viewed_at = None

        # Retrieve trakt `viewed_at` from item
        if type(t_item) is dict:
            t_viewed_at = t_item.get('last_watched_at')
        else:
            t_viewed_at = t_item.last_watched_at if t_item else None

        return p_viewed_at, t_viewed_at
