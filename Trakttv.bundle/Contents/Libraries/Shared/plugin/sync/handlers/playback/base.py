from plugin.sync.handlers.core import MediaHandler


class PlaybackHandler(MediaHandler):
    @staticmethod
    def get_operands(p_item, t_item):
        # Retrieve plex parameters
        if p_item is not None:
            p_duration = p_item.get('part', {}).get('duration')
            p_view_offset = p_item.get('settings', {}).get('view_offset')

            # Calculate progress in plex (if available)
            if p_duration is not None and p_view_offset is not None:
                # Calculate progress from duration and view offset
                p_progress = round((float(p_view_offset) / p_duration) * 100, 2)
            else:
                p_progress = None
        else:
            p_progress = None

        # Retrieve trakt progress from item
        if type(t_item) is dict:
            t_progress = t_item.get('progress')
        else:
            t_progress = t_item.progress if t_item else None

        return p_progress, t_progress
