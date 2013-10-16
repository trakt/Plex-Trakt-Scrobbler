class EventHandler(object):
    def __init__(self):
        self.handlers = []

    def subscribe(self, handler):
        self.handlers.append(handler)
        return self

    def unsubscribe(self, handler):
        self.handlers.remove(handler)
        return self

    def fire(self, *args, **kwargs):
        for handler in self.handlers:
            handler(*args, **kwargs)
