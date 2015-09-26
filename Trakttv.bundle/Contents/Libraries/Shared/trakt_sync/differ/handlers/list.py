from trakt_sync.differ.handlers.core.base import Handler


class List(Handler):
    name = 'list'

    def on_added(self, current):
        yield self.add(current)

    def on_removed(self, base):
        yield self.remove(base)

    def on_common(self, base, current):
        if base.index == current.index:
            return

        yield self.change((base, current))

    def properties(self, item):
        if type(item) is tuple:
            return {
                'index': self.properties_change(item, 'index')
            }

        return {
            'index': item.index
        }
