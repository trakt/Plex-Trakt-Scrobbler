from trakt_sync.cache.sources.core.base import Source
from trakt_sync.differ import ListDiffer, ListResult, ListsDiffer, ListsResult
import trakt_sync.cache.enums as enums

from dateutil.tz import tzutc
from trakt import Trakt
import logging
import trakt.objects

log = logging.getLogger(__name__)


class ListSource(Source):
    def __init__(self, main):
        super(ListSource, self).__init__(main)

        # Differs
        self._list_differ = ListDiffer()
        self._lists_differ = ListsDiffer()

    def refresh(self, username):
        if enums.Media.Lists not in self.media:
            return

        if enums.Data.Liked in self.data:
            # Refresh liked lists, yield changes
            for change in self.refresh_lists(username, enums.Data.Liked, Trakt['users'].likes('lists')):
                yield change

        if enums.Data.Personal in self.data:
            # Refresh personal lists, yield changes
            for change in self.refresh_lists(username, enums.Data.Personal, Trakt['users/*/lists'].get(username)):
                yield change

    def refresh_lists(self, username, data, lists):
        key = (enums.Media.Lists, data)

        # Resolve lists
        lists = dict([
            (t_list.id, t_list)
            for t_list in lists
        ])

        # Find changes
        collection = self.get_collection(username, *key)
        changes = self.diff(key, collection['store'], lists)

        if changes is not None:
            yield self._collection_key(*key), changes

        # Store lists in cache
        self.update_store((username, ) + key, lists)

        # Store list items in cache, yield changes
        for l in lists.itervalues():
            for change in self.refresh_list(username, data, l):
                yield change

    def refresh_list(self, username, data, t_list):
        key = (enums.Media.Lists, data, t_list.id)

        collection = self.get_collection(username, *key)
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

        # Find changes
        changes = self.diff(key, collection['store'], store)

        # Update collection
        self.update_store((username, ) + key, store)

        collection['timestamps'][timestamp_key] = current

        if changes is None:
            # No changes detected
            return

        yield self._collection_key(*key), changes

    def diff(self, key, base, current):
        media, data, list_id = (None, None, None)

        if len(key) == 2:
            media, data = key
        elif len(key) == 3:
            media, data, list_id = key
        else:
            log.warn('Unsupported key: %r', key)
            return None

        if not base:
            if not current:
                return None

            # No `base` data stored, assume all the `current` items have been added
            if media != enums.Media.Lists:
                raise Exception('Unknown media type: %r', media)

            if list_id is not None:
                result = ListResult(self._list_differ)
            else:
                result = ListsResult(self._lists_differ)

            # Update `result` with current items
            result.add(current)

            return result

        if media != enums.Media.Lists:
            raise Exception('Unknown media type: %r', media)

        if list_id is not None:
            result = self._list_differ.run(base, current)
        else:
            result = self._lists_differ.run(base, current)

        if not result.changes:
            return None

        return result

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

    def get_collection(self, username, media, data, id=None):
        key = self._storage_key(username, media, data, id)

        return super(ListSource, self).get_collection(*key)

    @staticmethod
    def _item_key(t_item):
        key = list(t_item.pk) if type(t_item.pk) is tuple else [t_item.pk]

        if type(t_item) in [trakt.objects.Movie, trakt.objects.Show]:
            return tuple(key)

        if type(t_item) in [trakt.objects.Season, trakt.objects.Episode]:
            key = list(t_item.keys[1]) + [str(x) for x in key]
            return tuple(key)

        raise ValueError('Unknown item: %r', t_item)

    @staticmethod
    def _collection_key(media, data, id=None):
        if id is None:
            return media, data

        return media, data, id

    @classmethod
    def _storage_key(cls, username, media, data, id=None):
        result = [
            username,
            enums.Media.get(media),
            enums.Data.get(data)
        ]

        if id:
            result.append(str(id))

        return tuple(result)
