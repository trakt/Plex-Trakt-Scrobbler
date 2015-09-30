from trakt_sync.differ.handlers.core.base import Handler


class Watchlist(Handler):
    name = 'watchlist'

    def on_added(self, current):
        if current.in_watchlist is True:
            yield self.add(current)
        elif current.in_watchlist is False:
            yield self.remove(current)

    def on_removed(self, base):
        if base.in_watchlist is True:
            yield self.remove(base)

    def on_common(self, base, current):
        if base.in_watchlist == current.in_watchlist:
            return

        if base.in_watchlist is None:
            yield self.add(current)
        elif current.in_watchlist is None:
            yield self.remove(base)
        else:
            yield self.change((base, current))

    def properties(self, item):
        if type(item) is tuple:
            return {
                'in_watchlist': self.properties_change(item, 'in_watchlist')
            }

        return {}
