from sync.sync_base import SyncBase
import time


class Synchronize(SyncBase):
    title = "Synchronize"

    def run(self, **kwargs):
        Log.Debug('Synchronize.run kwargs: %s' % kwargs)

        self.update_progress(0)

        for x in range(1, 11):
            if self.is_stopping():
                return False

            time.sleep(1)

            self.update_progress(x * 10)

        return True
