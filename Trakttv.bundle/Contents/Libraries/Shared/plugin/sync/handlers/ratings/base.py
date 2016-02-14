from plugin.sync.handlers.core import MediaHandler


class RatingsHandler(MediaHandler):
    @staticmethod
    def get_operands(p_item, t_item):
        # Retrieve plex rating from item
        if p_item is not None:
            p_rating = p_item.get('settings', {}).get('rating')
        else:
            p_rating = None

        # Convert rating to integer
        if p_rating is not None:
            p_rating = int(p_rating)

        # Retrieve trakt rating from item
        if type(t_item) is dict:
            t_rating = t_item.get('rating')
        else:
            t_rating = t_item.rating if t_item else None

        # Convert trakt `Rating` objects to plain rating values
        if type(t_rating) is tuple:
            t_rating = tuple([
                (r.value if r else None)
                for r in t_rating
            ])
        else:
            t_rating = t_rating.value if t_rating else None

        return p_rating, t_rating
