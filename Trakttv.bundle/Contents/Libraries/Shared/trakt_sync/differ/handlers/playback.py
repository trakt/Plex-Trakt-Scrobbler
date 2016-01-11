from trakt_sync.differ.handlers.core.base import Handler


class Playback(Handler):
    name = 'playback'

    def on_added(self, current):
        if current.progress is not None:
            yield self.add(current)

    def on_removed(self, base):
        if base.progress is not None:
            yield self.remove(base)

    def on_common(self, base, current):
        if base.progress == current.progress:
            return

        if base.progress is None:
            yield self.add(current)
        elif current.progress is None:
            yield self.remove(base)
        else:
            yield self.change((base, current))

    def properties(self, item):
        if type(item) is tuple:
            return {
                'progress': self.properties_change(item, 'progress'),

                'paused_at': self.properties_change(item, 'paused_at')
            }

        return {
            'progress': item.progress,

            'paused_at': item.paused_at
        }
