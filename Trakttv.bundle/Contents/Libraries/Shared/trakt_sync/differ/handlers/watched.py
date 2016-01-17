from trakt_sync.differ.handlers.core.base import Handler


class Watched(Handler):
    name = 'watched'

    def on_added(self, current):
        if current.is_watched is True:
            yield self.add(current)
        elif current.is_watched is False:
            yield self.remove(current)

    def on_removed(self, base):
        if base.is_watched is True:
            yield self.remove(base)

    def on_common(self, base, current):
        if base.is_watched == current.is_watched:
            return

        if base.is_watched is None:
            yield self.add(current)
        elif current.is_watched is None:
            yield self.remove(base)
        else:
            yield self.change((base, current))

    def properties(self, item):
        if type(item) is tuple:
            return {
                'is_watched': self.properties_change(item, 'is_watched'),

                'plays': self.properties_change(item, 'plays'),
                'last_watched_at': self.properties_change(item, 'last_watched_at')
            }

        return {
            'plays': item.plays,
            'last_watched_at': item.last_watched_at
        }
