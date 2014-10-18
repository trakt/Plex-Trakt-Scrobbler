from core.helpers import total_seconds
from core.logger import Logger
from core.numeric import ema
from sync.sync_task import SyncTaskStatistics
from datetime import datetime

log = Logger('sync.sync_statistics')


MESSAGES = {
    'pull.show': 'Pulling shows from trakt',
    'push.show': 'Pushing shows to trakt',

    'pull.movie': 'Pulling movies from trakt',
    'push.movie': 'Pushing shows to trakt'
}


class SyncStatistics(object):
    def __init__(self, manager):
        self.manager = manager

        self.active = []

        # Bind to handler status events
        for _, task in manager.handlers.items():
            self.bind(task)

    def bind(self, task):
        key = task.get_key()

        # Bind events
        task.on('started', lambda end: self.started(key, end))\
            .on('progress', lambda value: self.progress(key, value))\
            .on('finished', lambda: self.finished(key))

        # Bind child progress events
        for _, child in task.children.items():
            self.bind(child)

    def reset(self):
        if not self.manager.current:
            return

        self.manager.current.statistics = SyncTaskStatistics()

    def update(self):
        if not self.manager.current or not self.active:
            return

        st = self.manager.current.statistics
        if not st:
            return

        st.message = MESSAGES.get(self.key)

    def started(self, key, end, start=0):
        self.reset()

        self.active.append((key, start, end))
        self.update()

    def progress(self, key, value):
        if not self.manager.current:
            return

        if key != self.key:
            return

        stat = self.manager.current.statistics

        if not stat or self.offset is None:
            return

        value += self.offset
        progress = float(value) / self.end

        self.calculate_timing(stat, progress)

        # log.debug(
        #    '[%s] progress: %02d%%, estimated time remaining: ~%s seconds',
        #    key, progress * 100,
        #    round(stat.seconds_remaining, 2) if stat.seconds_remaining else '?'
        # )

        stat.progress = progress
        stat.last_update = datetime.utcnow()

    def calculate_timing(self, stat, cur_progress):
        if not stat.last_update:
            return

        progress_delta = cur_progress - (stat.progress or 0)
        delta_seconds = total_seconds(datetime.utcnow() - stat.last_update)

        # Calculate current speed (in [percent progress]/sec)
        cur_speed = delta_seconds / (progress_delta * 100)

        if stat.per_perc is None:
            # Start initially at first speed value
            stat.per_perc = cur_speed
        else:
            # Calculate EMA speed
            stat.per_perc = ema(cur_speed, stat.per_perc)

        # Calculate estimated time remaining
        stat.seconds_remaining = ((1 - cur_progress) * 100) * stat.per_perc

    def finished(self, key):
        self.reset()

        # Search for key in 'active' list and remove it
        for x, (k, _, _) in enumerate(self.active):
            if k != key:
                continue

            self.active.pop(x)
            break

        # Update task status (message)
        self.update()

    #
    # Active task properties
    #

    @property
    def key(self):
        if not self.active:
            return None

        key, _, _ = self.active[-1]

        return key

    @property
    def offset(self):
        if not self.active:
            return None

        _, start, _ = self.active[-1]

        return 0 - start

    @property
    def start(self):
        if not self.active:
            return None

        _, start, _ = self.active[-1]

        return start + self.offset

    @property
    def end(self):
        if not self.active:
            return None

        _, _, end = self.active[-1]

        return end + self.offset
