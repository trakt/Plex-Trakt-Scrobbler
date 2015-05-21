class Handler(object):
    name = None

    def __init__(self, differ):
        self._differ = differ

    def on_added(self, current):
        pass

    def on_removed(self, base):
        pass

    def on_common(self, base, current):
        pass

    def properties(self, item):
        raise NotImplementedError()

    def properties_change(self, (base, current), attribute):
        return getattr(base, attribute), getattr(current, attribute)

    def add(self, item):
        return list(self._differ.item_keys(item)), self.name, 'added', self.properties(item)

    def remove(self, item):
        return list(self._differ.item_keys(item)), self.name, 'removed', self.properties(item)

    def change(self, (base, current)):
        return list(self._differ.item_keys(base)), self.name, 'changed', self.properties((base, current))
