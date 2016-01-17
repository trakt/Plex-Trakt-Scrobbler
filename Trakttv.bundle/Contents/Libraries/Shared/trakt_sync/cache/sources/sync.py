from trakt_sync.cache.sources.core.base import Source
from trakt_sync.differ import MovieDiffer, MovieResult, ShowDiffer, ShowResult
import trakt_sync.cache.enums as enums

from dateutil.tz import tzutc
from trakt import Trakt
from trakt.core.helpers import from_iso8601
import logging

log = logging.getLogger(__name__)

COLLECTION_NAME_MAP = {
    'shows': {
        'collection':  ('episodes', 'collection'),
        'watched':     ('episodes', 'watched')
    }
}

COLLECTION_ENUM_MAP = {
    enums.Media.Shows: {
        enums.Data.Collection:  (enums.Media.Episodes, enums.Data.Collection),
        enums.Data.Watched:     (enums.Media.Episodes, enums.Data.Watched)
    }
}


class SyncSource(Source):
    def __init__(self, main):
        super(SyncSource, self).__init__(main)

        # Differs
        self._movie_differ = MovieDiffer()
        self._show_differ = ShowDiffer()

    def refresh(self, username):
        # Emit "started" event
        self.events.emit('refresh.sync.started', source='sync', total=self.steps())
        current_step = 0

        # Fetch sync activity timestamps
        activities = Trakt['sync'].last_activities(exceptions=True)

        # Refresh each data set
        for m in self.media:
            media = enums.Media.get(m)

            for d in self.data:
                data = enums.Data.get(d)

                if not self.exists(d, m):
                    # Unsupported media + data combination
                    continue

                # Update `current` progress, emit "progress" event
                self.events.emit('refresh.sync.progress', source='sync', current=current_step)
                current_step += 1

                # Retrieve collection from database
                collection = self.get_collection(username, media, data)
                timestamp_key = enums.Data.get_timestamp_key(d)

                # Retrieve current timestamp from trakt.tv
                current = self._get_timestamp(activities, d, m)

                # Determine if cached items are still valid
                last = collection['timestamps'][media].get(timestamp_key)

                if last and last.tzinfo is None:
                    # Missing "tzinfo", assume UTC
                    last = last.replace(tzinfo=tzutc())

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

                # Update collection
                self.update_store((username, media, data), store)

                collection['timestamps'][media][timestamp_key] = current

                if changes is None:
                    # No changes detected
                    continue

                # Return collection changes
                yield self._collection_key(m, d), changes

        # Emit "finished" event
        self.events.emit('refresh.sync.finished', source='sync', current=current_step)

    def steps(self):
        result = 0

        # Iterate over each data set and increment `result`
        for m in self.media:
            for d in self.data:
                if not self.exists(d, m):
                    # Unsupported media + data combination
                    continue

                result += 1

        return result

    def diff(self, media, data, base, current):
        if not base:
            if not current:
                return None

            # No `base` data stored, assume all the `current` items have been added
            if media == enums.Media.Movies:
                result = MovieResult(self._movie_differ)
            elif media in [enums.Media.Shows, enums.Media.Seasons, enums.Media.Episodes]:
                result = ShowResult(self._show_differ)
            else:
                raise Exception('Unknown media type: %r', media)

            # Update `result` with current items
            result.add(current)

            return result

        data_name = enums.Data.get(data)

        if media == enums.Media.Movies:
            result = self._movie_differ.run(base, current, handlers=[data_name])
        elif media in [enums.Media.Shows, enums.Media.Seasons, enums.Media.Episodes]:
            result = self._show_differ.run(base, current, handlers=[data_name])
        else:
            raise Exception('Unknown media type: %r', media)

        return result

    def fetch(self, data, media):
        interface = enums.Data.get_interface(data)
        method = enums.Media.get(media)

        func = self.fetch_func(data, media)

        if func is None:
            return None

        # Execute `func` (fetch data from trakt.tv)
        path = '/'.join([interface, method])

        log.info('Fetching "%s"', path)

        try:
            return func(exceptions=True)
        except NotImplementedError:
            log.warn('Unable to fetch "%s", not implemented', path)

    @staticmethod
    def fetch_func(data, media):
        if type(data) is not str:
            data = enums.Data.get_interface(data)

        if type(media) is not str:
            media = enums.Media.get(media)

        # Retrieve function (`method`) from `interface`
        return getattr(Trakt[data], media, None)

    @classmethod
    def exists(cls, data, media):
        func = cls.fetch_func(data, media)

        return func is not None

    @staticmethod
    def _get_timestamp(activities, data, media):
        method = enums.Media.get(media)

        if media in [enums.Media.Movies, enums.Media.Seasons, enums.Media.Episodes]:
            timestamps = activities[method]
        elif media == enums.Media.Shows:
            if data in [enums.Data.Collection, enums.Data.Playback, enums.Data.Watched, enums.Data.Watchlist]:
                # Map shows (collection, playback, watched, watchlist) -> episodes
                timestamps = activities['episodes']
            else:
                timestamps = activities[method]
        else:
            # unknown data/media combination
            raise ValueError()

        # Retrieve timestamp
        value = timestamps.get(
            enums.Data.get_timestamp_key(data)
        )

        # Parse timestamp
        return from_iso8601(value)

    def get_collection(self, username, media, data):
        key = self._storage_key(username, media, data)

        collection = super(SyncSource, self).get_collection(*key)

        if media not in collection['timestamps']:
            collection['timestamps'][media] = {}

        return collection

    @staticmethod
    def _collection_key(media, data):
        if media in COLLECTION_ENUM_MAP and data in COLLECTION_ENUM_MAP[media]:
            # Apply collection map
            media, data = COLLECTION_ENUM_MAP[media][data]

        return media, data

    @classmethod
    def _storage_key(cls, username, media, data):
        if media in COLLECTION_NAME_MAP and data in COLLECTION_NAME_MAP[media]:
            # Apply collection map
            media, data = COLLECTION_NAME_MAP[media][data]

        return username, media, data
