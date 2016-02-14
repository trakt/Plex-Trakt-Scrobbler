from trakt_sync.differ.handlers.core.base import Handler


class Collection(Handler):
    name = 'collection'

    def on_added(self, current):
        if current.is_collected is True:
            yield self.add(current)
        elif current.is_collected is False:
            yield self.remove(current)

    def on_removed(self, base):
        if base.is_collected is True:
            yield self.remove(base)

    def on_common(self, base, current):
        if base.is_collected == current.is_collected:
            return

        if base.is_collected is None:
            yield self.add(current)
        elif current.is_collected is None:
            yield self.remove(base)
        else:
            yield self.change((base, current))

    def properties(self, item):
        if type(item) is tuple:
            return {
                'is_collected': self.properties_change(item, 'is_collected'),

                'collected_at': self.properties_change(item, 'collected_at')
            }

        return {
            'collected_at': item.collected_at
        }
