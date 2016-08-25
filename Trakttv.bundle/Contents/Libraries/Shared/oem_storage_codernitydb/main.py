from oem_framework.core.elapsed import Elapsed
from oem_framework.models.core import ModelRegistry
from oem_storage_codernitydb.database import DatabaseCodernityDbStorage
from oem_storage_codernitydb.indices import MetadataKeyIndex, MetadataCollectionIndex, ItemKeyIndex, CollectionKeyIndex
from oem_framework.storage import ProviderStorage
from oem_framework.plugin import Plugin

from CodernityDB.database import RecordNotFound
from CodernityDB.database_super_thread_safe import SuperThreadSafeDatabase
from semantic_version import Version
import logging
import os

log = logging.getLogger(__name__)


class CodernityDbStorage(ProviderStorage, Plugin):
    __key__ = 'codernitydb'

    def __init__(self, path=None):
        super(CodernityDbStorage, self).__init__()

        self.path = path

        self.database = SuperThreadSafeDatabase(path)

        if os.path.exists(path):
            self.database.open()

    #
    # Provider methods
    #

    def create(self, source, target):
        if os.path.exists(self.path):
            return True

        # Create database
        self.database.create()

        # Add indices
        self.database.add_index(CollectionKeyIndex(self.database.path,      'collection_key'))
        self.database.add_index(MetadataKeyIndex(self.database.path,        'metadata_key'))
        self.database.add_index(MetadataCollectionIndex(self.database.path, 'metadata_collection'))
        self.database.add_index(ItemKeyIndex(self.database.path,            'item_key'))

        return True

    def open_database(self, source, target, database=None):
        return ModelRegistry['Database'].load(
            DatabaseCodernityDbStorage.open(self, source, target, database),
            source, target
        )

    #
    # Collection methods
    #

    def has_collection(self, source, target):
        try:
            self.database.get('collection_key', (source, target))
            return True
        except RecordNotFound:
            pass

        return False

    def get_collection_version(self, source, target):
        try:
            item = self.database.get('collection_key', (source, target), with_doc=True)

            if not item or 'doc' not in item:
                return None

            return Version(item['doc'].get('version'))
        except RecordNotFound:
            pass

        return None

    @Elapsed.track
    def update_collection(self, source, target, version):
        # Retrieve current item
        try:
            current = self.database.get('collection_key', (source, target), with_doc=True)

            if 'doc' in current:
                current = current['doc']
            else:
                current = None
        except RecordNotFound:
            current = None

        # Build collection metadata
        item = {
            '_': {
                't': 'collection',

                'c': {
                    's': source,
                    't': target
                }
            },

            # Collection attributes
            'version': str(version)
        }

        # Add current item identifier
        if current and '_id' in current and '_rev' in current:
            item['_id'] = current['_id']
            item['_rev'] = current['_rev']

        # Update database
        if current:
            # Update existing item
            try:
                self.database.update(item)
            except Exception, ex:
                log.warn('Unable to update collection: %s', ex, exc_info=True)
                return False

            log.debug('[%s -> %s] Updated collection', source, target)
            return True

        # Insert new item
        try:
            self.database.insert(item)
        except Exception, ex:
            log.warn('Unable to insert collection: %s', ex, exc_info=True)
            return False

        log.debug('[%s -> %s] Inserted collection', source, target)
        return True

    #
    # Index methods
    #

    @Elapsed.track
    def update_index(self, source, target, response):
        # Retrieve current items
        current_items = self.database.get_many('metadata_collection', (source, target), with_doc=True)

        # Decode response
        latest_index = self.format.decode(
            ModelRegistry['Index'],
            self.format.load_string(response.content),
            children=False
        )

        if 'items' not in latest_index:
            return False

        latest_items = latest_index['items']

        # Update items
        for current in current_items:
            # Retrieve item document
            doc = current.get('doc')

            if not doc:
                continue

            key = doc.get('_', {}).get('k')

            if not key:
                continue

            # Find matching item in `data`
            latest = latest_items.get(key)

            if not latest:
                # Delete item from database
                try:
                    self.database.delete(doc)
                except Exception, ex:
                    log.warn('Unable to delete item: %s', ex, exc_info=True)

                continue

            # Set item identifiers
            latest['_id'] = doc['_id']
            latest['_rev'] = doc['_rev']

            # Update item in database
            try:
                self.database.update(self._build_metadata(source, target, key, latest))
            except Exception, ex:
                log.warn('Unable to update item: %s', ex, exc_info=True)
                continue

            # Remove item from `index_latest` (to ensure it isn't processed twice)
            del latest_items[key]

        # Insert items
        if not latest_items:
            return True

        log.debug('Inserting %d items', len(latest_items))

        for key, item in latest_items.items():
            try:
                self.database.insert(self._build_metadata(source, target, key, item))
            except Exception, ex:
                log.warn('Unable to insert item: %s', ex, exc_info=True)
                continue

        return True

    def _build_metadata(self, source, target, key, item):
        # Set attributes
        item['_'] = {
            't': 'metadata',
            'k': key,

            'c': {
                's': source,
                't': target
            }
        }

        if self.format.__key__.startswith('minimize+'):
            item['_']['e'] = True

        return item

    #
    # Item methods
    #

    def has_item(self, source, target, key, metadata=None):
        try:
            # Retrieve current item from database
            item = self.database.get('item_key', (source, target, key), with_doc=True)

            # Validate item
            if metadata is not None:
                # Retrieve current item timestamp
                updated_at = item.get('doc', {}).get('_', {}).get('u')

                if updated_at is None:
                    return False

                # Ensure item is up to date
                if updated_at >= metadata.updated_at:
                    return True

                return False

            # Item exists in database
            return True
        except RecordNotFound:
            pass

        # Unable to find item in database
        return False

    @Elapsed.track
    def update_item(self, source, target, key, response, metadata):
        # Retrieve current item
        try:
            current = self.database.get('item_key', (source, target, key), with_doc=True)

            if 'doc' in current:
                current = current['doc']
            else:
                current = None
        except RecordNotFound:
            current = None

        # Decode response
        item = self.format.decode(
            ModelRegistry['Item'],
            self.format.load_string(response.content),
            media=metadata.media
        )

        # Add current item identifier
        if current and '_id' in current and '_rev' in current:
            item['_id'] = current['_id']
            item['_rev'] = current['_rev']

        # Set attributes
        item['_'] = {
            't': 'item',
            'k': key,
            'u': metadata.updated_at,

            'c': {
                's': source,
                't': target
            }
        }

        # Update database
        if current:
            # Update existing item
            try:
                self.database.update(item)
            except Exception, ex:
                log.warn('Unable to update item: %s', ex, exc_info=True)
                return False

            log.debug('[%s -> %s] Updated item %r (updated_at: %r)', source, target, key, metadata.updated_at)
            return True

        # Insert new item
        try:
            self.database.insert(item)
        except Exception, ex:
            log.warn('Unable to insert item: %s', ex, exc_info=True)
            return False

        log.debug('[%s -> %s] Inserted item %r (updated_at: %r)', source, target, key, metadata.updated_at)
        return True
