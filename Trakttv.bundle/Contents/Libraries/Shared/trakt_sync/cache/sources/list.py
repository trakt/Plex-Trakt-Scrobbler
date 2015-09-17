from trakt_sync.cache.sources.core.base import Source
import trakt_sync.cache.enums as enums

from dateutil.tz import tzutc
from trakt import Trakt
import logging
import trakt.objects

log = logging.getLogger(__name__)


class ListSource(Source):
    def refresh(self, username):
        # Refresh liked lists, yield changes
        for change in self.refresh_lists(username, enums.Data.ListLiked, Trakt['users'].likes('lists')):
            yield change

        # Refresh personal lists, yield changes
        for change in self.refresh_lists(username, enums.Data.ListPersonal, Trakt['users/*/lists'].get(username)):
            yield change

    def refresh_lists(self, username, data, lists):
        # Store lists in cache
        self.update_store((username, data), dict([
            (t_list.id, t_list)
            for t_list in lists
        ]))

        # Store list items in cache, yield changes
        for l in lists:
            for change in self.refresh_list(username, data, l):
                yield change

    def refresh_list(self, username, data, t_list):
        collection = self.get_collection(username, data, t_list.id)
        timestamp_key = enums.Data.get_timestamp_key(data)

        # Retrieve current timestamp from trakt.tv
        current = getattr(t_list, timestamp_key)

        # Determine if cached items are still valid
        last = collection['timestamps'].get(timestamp_key)

        if last and last.tzinfo is None:
            # Missing "tzinfo", assume UTC
            last = last.replace(tzinfo=tzutc())

        if last and last == current:
            # Latest data already cached
            return

        # Fetch latest data
        store = self.fetch(t_list)

        if store is None:
            # Unable to retrieve data
            return

        # TODO Find changes
        changes = None

        # Update collection
        self.update_store((username, data, t_list.id), store)

        collection['timestamps'][timestamp_key] = current

        if changes is None:
            # No changes detected
            return

        yield (None, enums.Data.ListLiked), None

    def get_collection(self, username, data, id=None):
        key = self._storage_key(username, data, id)

        return super(ListSource, self).get_collection(*key)

    def fetch(self, t_list):
        log.debug('Fetching list: %r', t_list)

        try:
            return dict([
                (self._item_key(t_item), t_item)
                for t_item in t_list.items()
            ])
        except Exception, ex:
            log.warn('Unable to retrieve items for list %r - %s', t_list, ex, exc_info=True)

        return None

    @staticmethod
    def _item_key(t_item):
        key = list(t_item.pk) if type(t_item.pk) is tuple else [t_item.pk]

        if type(t_item) in [trakt.objects.Movie, trakt.objects.Show]:
            return tuple(key)

        if type(t_item) in [trakt.objects.Season, trakt.objects.Episode]:
            key = list(t_item.keys[1]) + [str(x) for x in key]
            return tuple(key)

        raise ValueError('Unknown item: %r', t_item)

    @classmethod
    def _storage_key(cls, username, data, id=None):
        result = [username]
        result.extend(enums.Data.get(data))

        if id:
            result.append(str(id))

        return tuple(result)
