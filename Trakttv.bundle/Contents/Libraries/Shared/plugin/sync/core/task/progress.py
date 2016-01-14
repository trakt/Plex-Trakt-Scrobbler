from datetime import datetime
import inspect
import logging

log = logging.getLogger(__name__)


class SyncProgressBase(object):
    speed_smoothing = 0.75

    def __init__(self, tag):
        self.tag = tag

        self.current = None
        self.maximum = None
        self.speed = None

        self.started_at = None
        self.ended_at = None

    @property
    def elapsed(self):
        if self.started_at and self.ended_at:
            return (self.ended_at - self.started_at).total_seconds()

        if self.started_at:
            return (datetime.utcnow() - self.started_at).total_seconds()

        return None

    @property
    def percent(self):
        raise NotImplementedError

    @property
    def per_second(self):
        elapsed = self.elapsed

        if not elapsed:
            return None

        return float(self.current) / elapsed

    @property
    def remaining(self):
        if self.maximum is None or self.current is None:
            return None

        value = self.maximum - self.current

        if value < 0:
            return 0

        return value

    @property
    def remaining_seconds(self):
        remaining = self.remaining

        if remaining is None or self.speed is None:
            return None

        return float(remaining) / self.speed

    def add(self, delta):
        if not delta:
            return

        # Update group maximum
        self.maximum += delta

    def start(self, maximum=0):
        self.current = 0
        self.maximum = maximum

        self.speed = None

        self.started_at = datetime.utcnow()
        self.ended_at = None

    def step(self, delta=1):
        if not delta:
            return

        # Update group position
        self.current += delta

        # Update average syncing speed
        self.update_speed()

    def stop(self):
        self.ended_at = datetime.utcnow()

    def update_speed(self):
        if self.speed is None:
            # First sample, set to current `per_second`
            self.speed = self.per_second
            return

        # Calculate average syncing speed (EMA)
        self.speed = self.speed_smoothing * self.per_second + (1 - self.speed_smoothing) * self.speed


class SyncProgress(SyncProgressBase):
    def __init__(self, task):
        super(SyncProgress, self).__init__('root')

        self.task = task

        self.groups = None

    @property
    def percent(self):
        if not self.groups:
            return 0.0

        samples = []

        for group in self.groups.itervalues():
            samples.append(group.percent)

        return sum(samples) / len(samples)

    def group(self, *tag):
        # Resolve tag to string
        tag = self._resolve_tag(tag)

        # Return existing progress group (if available)
        if tag in self.groups:
            return self.groups[tag]

        # Construct new progress group
        group = self.groups[tag] = SyncProgressGroup(self, tag)
        group.start()

        log.debug('constructed group (tag: %r)', tag)
        return group

    def start(self, maximum=0):
        super(SyncProgress, self).start(maximum)

        # Reset active groups
        self.groups = {}

        log.debug('[%-40s] started (maximum: %s)', self.tag[-40:], self.maximum)

    def step(self, delta=1):
        super(SyncProgress, self).step(delta)

        log.debug('[%-40s] stepped [%s/%s - %s]', self.tag[-40:], self.current, self.maximum, self.percent)

    def stop(self):
        super(SyncProgress, self).stop()

        log.debug('[%-40s] stopped [%s/%s - %s]', self.tag[-40:], self.current, self.maximum, self.percent)

        for tag, group in self.groups.items():
            log.debug('[%s] %r', tag, group)

    @staticmethod
    def _resolve_tag(tag):
        if isinstance(tag, (str, unicode)):
            return tag

        # Resolve tag
        if inspect.isclass(tag[0]):
            cls = tag[0]
            path = '%s.%s' % (cls.__module__, cls.__name__)

            tag = [path] + list(tag[1:])

        # Convert tag to string
        return ':'.join(tag)


class SyncProgressGroup(SyncProgressBase):
    def __init__(self, root, tag):
        super(SyncProgressGroup, self).__init__(tag)

        self.root = root

    @property
    def percent(self):
        if self.maximum is None or self.current is None:
            return 0.0

        if self.maximum < 1:
            return 0.0

        value = (float(self.current) / self.maximum) * 100

        if value > 100:
            return 100.0

        return value

    def add(self, delta):
        super(SyncProgressGroup, self).add(delta)

        # Update root maximum
        self.root.add(delta)

    def step(self, delta=1):
        super(SyncProgressGroup, self).step(delta)

        log.debug('[%-40s] stepped [%s/%s - %s]', self.tag[-40:], self.current, self.maximum, self.percent)

        # Update root progress
        self.root.step(delta)

    def __repr__(self):
        return '<SyncProgressGroup %s/%s - %s (speed: %r)>' % (
            self.current,
            self.maximum,
            self.percent,
            self.speed
        )
