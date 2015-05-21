from trakt_sync.differ.handlers.core.base import Handler


class Ratings(Handler):
    name = 'ratings'

    def on_added(self, current):
        if current.rating is not None:
            yield self.add(current)

    def on_removed(self, base):
        if base.rating is not None:
            yield self.remove(base)

    def on_common(self, base, current):
        if base.rating == current.rating:
            return

        if base.rating is None:
            yield self.add(current)
        elif current.rating is None:
            yield self.remove(base)
        else:
            yield self.change((base, current))

    def properties(self, item):
        if type(item) is tuple:
            return {
                'rating': self.properties_change(item, 'rating')
            }

        return {
            'rating': item.rating
        }
