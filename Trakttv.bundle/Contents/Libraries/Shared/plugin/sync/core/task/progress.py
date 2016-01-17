from plugin.core.environment import Environment

from datetime import datetime
import inspect
import logging

log = logging.getLogger(__name__)


class SyncProgressBase(object):
    speed_smoothing = 0.5

    def __init__(self, tag):
        self.tag = tag

        self.current = 0
        self.maximum = 0

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
    def remaining_seconds(self):
        raise NotImplementedError

    def add(self, delta):
        if not delta:
            return

        # Update group maximum
        self.maximum += delta

    def start(self):
        self.started_at = datetime.utcnow()
        self.ended_at = None

    def step(self, delta=1):
        if not delta:
            return

        if not self.started_at:
            self.start()

        # Update group position
        self.current += delta

    def stop(self):
        self.ended_at = datetime.utcnow()

    def _ema(self, value, previous, smoothing):
        if smoothing is None:
            # Use default smoothing value
            smoothing = self.speed_smoothing

        # Calculate EMA
        return smoothing * value + (1 - smoothing) * previous


class SyncProgress(SyncProgressBase):
    def __init__(self, task):
        super(SyncProgress, self).__init__('root')

        self.task = task

        self.groups = None
        self.group_speeds = None

    @property
    def percent(self):
        if not self.groups:
            return 0.0

        samples = []

        for group in self.groups.itervalues():
            samples.append(group.percent)

        return sum(samples) / len(samples)

    @property
    def remaining_seconds(self):
        if not self.groups:
            return 0.0

        samples = []

        for group in self.groups.itervalues():
            remaining_seconds = group.remaining_seconds

            if remaining_seconds is None:
                continue

            samples.append(remaining_seconds)

        return sum(samples)

    def group(self, *tag):
        if self.groups is None:
            raise Exception("Progress tracking hasn't been started")

        # Resolve tag to string
        tag = self._resolve_tag(tag)

        # Return existing progress group (if available)
        if tag in self.groups:
            return self.groups[tag]

        # Construct new progress group
        group = self.groups[tag] = SyncProgressGroup(self, tag)
        return group

    def start(self):
        super(SyncProgress, self).start()

        # Reset active groups
        self.groups = {}

        # Retrieve group speeds
        self.group_speeds = Environment.dict['sync.progress.group_speeds'] or {}

    def stop(self):
        super(SyncProgress, self).stop()

        # Save progress statistics
        self.save()

    def save(self):
        # Update group speeds
        self.group_speeds = dict([
            (group.tag, self._group_speed(group))
            for group in self.groups.itervalues()
        ])

        # Save to plugin dictionary
        Environment.dict['sync.progress.group_speeds'] = self.group_speeds

    def _group_speed(self, group):
        if not group.speed_min:
            # No group speed calculated yet
            return

        speed = self.group_speeds.get(group.tag)

        if not speed:
            # First sample
            return group.speed_min

        # Calculate EMA for group speed
        return self._ema(group.speed_min, speed, self.speed_smoothing)

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

        # Retrieve average group speed
        self.speed = self.root.group_speeds.get(self.tag)
        self.speed_min = None

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
        super(SyncProgressGroup, self).add(delta)

        # Update root maximum
        self.root.add(delta)

    def step(self, delta=1):
        super(SyncProgressGroup, self).step(delta)

        # Update average syncing speed
        self.update_speed()

        # Update root progress
        self.root.step(delta)

    def update_speed(self):
        if not self.per_second:
            # No steps emitted yet
            return

        if not self.speed:
            # First sample, set to current `per_second`
            self.speed = self.per_second
            return

        # Calculate average syncing speed (EMA)
        self.speed = self._ema(self.per_second, self.speed, self.speed_smoothing)

        # Update minimum speed
        if self.speed_min is None:
            # First sample
            self.speed_min = self.speed
        elif self.speed < self.speed_min:
            # New minimum speed reached
            self.speed_min = self.speed

    def __repr__(self):
        return '<SyncProgressGroup %s/%s - %.02f%% (remaining_seconds: %.02f, speed: %.02f, speed_min: %.02f)>' % (
            self.current,
            self.maximum,
            self.percent or 0,

            self.remaining_seconds or 0,
            self.speed or 0,
            self.speed_min or 0
        )
