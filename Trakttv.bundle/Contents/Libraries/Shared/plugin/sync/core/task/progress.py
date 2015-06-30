from datetime import datetime
import logging

log = logging.getLogger(__name__)


class SyncProgress(object):
    speed_smoothing = 0.75

    def __init__(self, task):
        self.task = task

        self._current = None
        self._maximum = None

        self._started_at = None
        self._ended_at = None

        self._speed = None

    @property
    def elapsed(self):
        if self._started_at and self._ended_at:
            return (self._ended_at - self._started_at).total_seconds()

        if self._started_at:
            return (datetime.utcnow() - self._started_at).total_seconds()

        return None

    @property
    def per_second(self):
        elapsed = self.elapsed

        if not elapsed:
            return None

        return float(self._current) / elapsed

    @property
    def percent(self):
        if self._maximum is None or self._current is None:
            return None

        if self._maximum < 1:
            return None

        return (float(self._current) / self._maximum) * 100

    @property
    def remaining(self):
        if self._maximum is None or self._current is None:
            return None

        return self._maximum - self._current

    @property
    def remaining_seconds(self):
        remaining = self.remaining

        if remaining is None or self._speed is None:
            return None

        return float(remaining) / self._speed

    def start(self, maximum):
        self._current = 0
        self._maximum = maximum

        self._started_at = datetime.utcnow()
        self._ended_at = None

        self._speed = None

    def step(self, delta=1):
        if self._current is None:
            self._current = 0

        self._current += delta

        # Update average syncing speed
        self.update_speed()

    def update_speed(self):
        if self._speed is None:
            # First sample, set to current `per_second`
            self._speed = self.per_second
            return

        # Calculate average syncing speed (EMA)
        self._speed = self.speed_smoothing * self.per_second + (1 - self.speed_smoothing) * self._speed

    def stop(self):
        self._ended_at = datetime.utcnow()
