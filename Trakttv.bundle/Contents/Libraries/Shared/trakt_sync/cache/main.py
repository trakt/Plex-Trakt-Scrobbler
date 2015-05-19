import trakt_sync.cache.enums as enums

from trakt import Trakt
from trakt.core.helpers import from_iso8601


class Cache(object):
    Data = enums.Data
    Media = enums.Media

    def __init__(self, media, data, storage):
        self.storage = storage

        self.collections = self.storage('collections')
        self.stores = {}

        self.media = Cache.Media.parse(media)
        self.data = Cache.Data.parse(data)

    def refresh(self, username):
        activities = Trakt['sync'].last_activities()

        for m in self.media:
            media = Cache.Media.get(m)

            for d in self.data:
                collection = self._get_collection(username, media)

                timestamp_key = Cache.Data.get_timestamp_key(d)

                current = self._get_timestamp(activities, d, m)
                last = collection['timestamps'][media].get(timestamp_key)

                if last and last == current:
                    # Latest data already cached
                    continue

                # Fetch latest data
                store = self.fetch(d, m)

                if store is None:
                    continue

                # Find changes
                changes = self.diff(collection['store'], store)

                # Update timestamp in cache to `current`
                # collection = self._get_collection(username, media)
                # collection['store'].update(store)
                # collection['timestamps'][media][timestamp_key] = current

                yield (m, d), changes

    def fetch(self, data, media):
        interface = Cache.Data.get_interface(data)
        method = Cache.Media.get(media)

        # Retrieve function (`method`) from `interface`
        func = getattr(Trakt[interface], method, None)

        if func is None:
            return None

        # Execute `func` (fetch data from trakt.tv)
        print 'Fetching "%s"' % '/'.join([interface, method])

        try:
            return func(exceptions=True)
        except Exception, ex:
            print type(ex), ex

        return None

    def diff(self, last_items, current_items):
        if not last_items:
            # No `last` data stored
            return current_items, {}

        # Retrieve keys
        keys_last = last_items.archive.keys()
        keys_current = current_items.keys()

        # Find added/removed keys
        keys_added = [k for k in keys_current if k not in keys_last]
        keys_removed = [k for k in keys_last if k not in keys_current]

        # TODO find changes
        return dict([
            (k, current_items[k]) for k in keys_added
        ]), dict([
            (k, last_items[k]) for k in keys_removed
        ])

    def __getitem__(self, key):
        collection = self._get_collection(*key)

        return collection['store']

    @staticmethod
    def _build_key(username, media):
        if media in ['seasons', 'episodes']:
            media = 'shows'

        return username, media

    def _get_collection(self, username, media):
        key = self._build_key(username, media)

        if key not in self.collections:
            self.collections[key] = {}

        collection = self.collections[key]

        collection['store'] = self._get_store(username, media)

        if 'timestamps' not in collection:
            collection['timestamps'] = {}

        if media not in collection['timestamps']:
            collection['timestamps'][media] = {}

        return collection

    def _get_store(self, username, media):
        key = self._build_key(username, media)

        if key not in self.stores:
            self.stores[key] = self.storage('stores.%s.%s' % (username, media))

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
