class SyncBase(object):
    title = "Unknown"
    children = []

    def __init__(self):
        # Activate children and create dictionary map
        self.children = [x() for x in self.children]

    def run(self):
        # Run sub functions (starting with 'run_')
        sub_functions = [(x, getattr(self, x)) for x in dir(self) if x.startswith('run_')]

        for name, func in sub_functions:
            Log.Debug('Running sub-function in task %s with name "%s"' % (self, name))
            func()

        # Run child tasks
        for child in self.children:
            Log.Debug('Running child task %s' % child)
            child.run()

    @staticmethod
    def update_progress(current, start=0, end=100):
        raise ReferenceError()

    @staticmethod
    def is_stopping():
        raise ReferenceError()
