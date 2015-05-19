class Differ(object):
    handlers = None

    def run(self, base, current):
        raise NotImplementedError

    def process_added(self, current):
        for h in self.handlers:
            for action in h.on_added(current):
                yield action

    def process_removed(self, base):
        for h in self.handlers:
            for action in h.on_removed(base):
                yield action

    def process_common(self, base, current):
        for h in self.handlers:
            for action in h.on_common(base, current):
                yield action

    @staticmethod
    def store_action(changes, key, collection, action, properties=None):
        if collection not in changes:
            changes[collection] = {}

        if action not in changes[collection]:
            changes[collection][action] = {}

        changes[collection][action][key] = properties

    @classmethod
    def store_actions(cls, changes, actions):
        for action in actions:
            cls.store_action(changes, *action)

    @classmethod
    def store_child(cls, changes, key, media, data):
        if not data:
            return

        if media not in changes:
            changes[media] = {}

        changes[media][key] = data
