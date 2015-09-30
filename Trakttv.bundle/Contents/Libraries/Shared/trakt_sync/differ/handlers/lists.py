from trakt_sync.differ.handlers.core.base import Handler


class Lists(Handler):
    name = 'lists'

    def on_added(self, current):
        yield self.add(current)

    def on_removed(self, base):
        yield self.remove(base)

    def on_common(self, base, current):
        if base.updated_at == current.updated_at:
            return

        yield self.change((base, current))

    def properties(self, item):
        if type(item) is tuple:
            return {
                'updated_at': self.properties_change(item, 'updated_at')
            }

        return {
            'updated_at': item.updated_at
        }
