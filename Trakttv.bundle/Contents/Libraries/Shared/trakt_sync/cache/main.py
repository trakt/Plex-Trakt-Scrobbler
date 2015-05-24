from trakt_sync.differ import MovieDiffer, ShowDiffer
import trakt_sync.cache.enums as enums

from trakt import Trakt
from trakt.core.helpers import from_iso8601
import logging

log = logging.getLogger(__name__)


class Cache(object):
    Data = enums.Data
    Media = enums.Media

    def __init__(self, media, data, storage):
        self.storage = storage

        self.collections = self.storage('collections')
        self.stores = {}

        self.media = Cache.Media.parse(media)
        self.data = Cache.Data.parse(data)

        # Differs
        self._movie_differ = MovieDiffer()
        self._show_differ = ShowDiffer()

    def refresh(self, username):
        activities = Trakt['sync'].last_activities()

        for m in self.media:
            media = Cache.Media.get(m)

            for d in self.data:
                data = Cache.Data.get(d)

                if not self.exists(d, m):
                    # Unsupported media + data combination
                    continue

                collection = self._get_collection(username, media, data)

                timestamp_key = Cache.Data.get_timestamp_key(d)

                current = self._get_timestamp(activities, d, m)
                last = collection['timestamps'][media].get(timestamp_key)

                if last and last == current:
                    # Latest data already cached
                    continue

                # Fetch latest data
                store = self.fetch(d, m)

                if store is None:
                    # Unable to retrieve data
                    continue

                # Find changes
                changes = self.diff(m, d, collection['store'], store)

                # Update store
                self.update_store((username, media, data), store)

                # Update timestamp in cache to `current`
                collection['timestamps'][media][timestamp_key] = current

                if changes is None:
                    # No changes detected
                    continue

                yield (m, d), changes

    def fetch(self, data, media):
        interface = Cache.Data.get_interface(data)
        method = Cache.Media.get(media)

        func = self.fetch_func(data, media)

        if func is None:
            return None

        # Execute `func` (fetch data from trakt.tv)
        print 'Fetching "%s"' % '/'.join([interface, method])

        try:
            return func(exceptions=True)
        except Exception, ex:
            print type(ex), ex

        return None

    @staticmethod
    def fetch_func(data, media):
        if type(data) is not str:
            data = Cache.Data.get_interface(data)

        if type(media) is not str:
            media = Cache.Media.get(media)

        # Retrieve function (`method`) from `interface`
        return getattr(Trakt[data], media, None)

    @classmethod
    def exists(cls, data, media):
        func = cls.fetch_func(data, media)

        return func is not None

    def diff(self, media, data, base, current):
        if not base:
            if not current:
                return None

            # No `base` data stored, assume all the `current` items have been added
            return {
                'added': current
            }

        data_name = Cache.Data.get(data)

        if media == Cache.Media.Movies:
            result = self._movie_differ.run(base, current, handlers=[data_name])
        elif media in [Cache.Media.Shows, Cache.Media.Seasons, Cache.Media.Episodes]:
            result = self._show_differ.run(base, current, handlers=[data_name])
        else:
            raise Exception('Unknown media type: %r', media)

        return result.get(data_name)

    def update_store(self, (username, media, data), current):
        collection = self._get_collection(username, media, data)
        collection_keys = set(collection['store'].keys())

        # Add + Update items
        collection['store'].update(current)

        # Delete items
        collection['store'].delete(collection_keys - set(current.keys()))

    def __getitem__(self, key):
        collection = self._get_collection(*key)

        return collection['store']

    @staticmethod
    def _build_key(username, media, data):
        return username, media, data

    def _get_collection(self, username, media, data):
        key = self._build_key(username, media, data)

        if key not in self.collections:
            self.collections[key] = {}

        collection = self.collections[key]

        collection['store'] = self._get_store(username, media, data)

        if 'timestamps' not in collection:
            collection['timestamps'] = {}

        if media not in collection['timestamps']:
            collection['timestamps'][media] = {}

        return collection

    def _get_store(self, username, media, data):
        key = self._build_key(username, media, data)

        if key not in self.stores:
            self.stores[key] = self.storage('stores.%s.%s.%s' % (username, media, data))

        return self.stores[key]

    @staticmethod
    def _get_timestamp(activities, data, media):
        method = Cache.Media.get(media)

        if media in [Cache.Media.Movies, Cache.Media.Seasons, Cache.Media.Episodes]:
            timestamps = activities[method]
        elif media == Cache.Media.Shows:
            if data in [Cache.Data.Collection, Cache.Data.Playback, Cache.Data.Watched, Cache.Data.Watchlist]:
                # Map shows (collection, playback, watched, watchlist) -> episodes
                timestamps = activities['episodes']
            else:
                timestamps = activities[method]
        else:
            # unknown data/media combination
            raise ValueError()

        # Retrieve timestamp
        value = timestamps.get(
            Cache.Data.get_timestamp_key(data)
        )

        # Parse timestamp
        return from_iso8601(value)
