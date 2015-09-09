import threading
import time

local = threading.local()


class Sample(object):
    def __init__(self, key, root=None):
        self.key = key
        self._root = root

        self.children = {}
        self.parent = None

        # Timestamps
        self.started_at = None
        self.ended_at = None

        # Result
        self.elapsed = None
        self.success = None

    @property
    def percent(self):
        if self.parent is None or self.parent.elapsed == 0:
            return None

        return (float(self.elapsed) / self.parent.elapsed) * 100

    @classmethod
    def aggregate(cls, key, samples, parent=None):
        result = Sample(
            key=key,
            root=parent._root if parent else None
        )
        result.parent = parent

        result.elapsed = 0
        result.success = True

        for sample in samples:
            for key, samples in sample.children.items():
                if key not in result.children:
                    result.children[key] = []

                result.children[key] += samples

            # Timestamps
            if result.started_at is None or sample.started_at < result.started_at:
                result.started_at = sample.started_at

            if result.ended_at is None or sample.ended_at > result.ended_at:
                result.ended_at = sample.ended_at

            # Result
            if not sample.success:
                result.success = False

            result.elapsed += sample.elapsed

        return result

    def aggregate_children(self):
        for key in list(self.children.keys()):
            if len(self.children[key]) < 2:
                continue

            self.children[key] = [
                Sample.aggregate(key, self.children[key], parent=self)
            ]

    def append_child(self, sample):
        # Set parent
        sample.parent = self

        # Append to children list
        if sample.key not in self.children:
            self.children[sample.key] = []

        self.children[sample.key].append(sample)

    def __enter__(self):
        self.started_at = time.time()

        # Ensure thread local stack exists
        if not hasattr(local, 'elapsed_stack'):
            local.elapsed_stack = []

        # Store sample in parent children
        if local.elapsed_stack:
            local.elapsed_stack[-1].append_child(self)
        elif self._root is not None:
            self._root.append(self)
        else:
            raise ValueError('Unable to find parent container')

        # Store sample in thread local
        local.elapsed_stack.append(self)

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.ended_at = time.time()
        self.elapsed = self.ended_at - self.started_at

        self.success = exc_type is None

        # Remove sample from thread local
        if not hasattr(local, 'elapsed_stack'):
            local.elapsed_stack = []

        local.elapsed_stack.remove(self)

    def __repr__(self):
        return '<Sample key: %r>' % (self.key, )

    def __str__(self):
        return self.__repr__()


class DummySample(object):
    def __init__(self):
        pass

    def __enter__(self):
        pass

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass
