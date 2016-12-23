from plugin.sync.core.enums import SyncData, SyncMode
from plugin.sync.modes.core.base import Mode

from trakt_sync.cache.main import Cache


class Base(Mode):
    mode = SyncMode.FastPull

    def iter_changes(self, media, pk):
        for key, result in self.trakt.changes:
            c_media, c_data = key[0:2]

            if c_media != media:
                # Ignore changes that aren't for `media`
                continue

            if c_data == SyncData.Watchlist:
                # Ignore watchlist data
                continue

            if not self.is_data_enabled(c_data):
                # Data type has been disabled
                continue

            data_name = Cache.Data.get(c_data)

            if data_name not in result.changes:
                # No changes for collection
                continue

            for c_action, items in result.changes[data_name].items():
                t_item = items.get(pk)

                if t_item is None:
                    # No item found in changes
                    continue

                yield c_data, c_action, t_item

    def should_pull(self, p_id, p_added_at):
        if not self.current.kwargs.get('pull'):
            return False

        pull = self.current.kwargs['pull']

        # Check `p_id` is inside the `ids` parameter
        if p_id in pull.get('ids', set()):
            return True

        # Check `p_added_at` timestamp is after the `created_since` parameter
        if p_added_at and pull.get('created_since') and p_added_at > pull['created_since']:
            return True

        return False
