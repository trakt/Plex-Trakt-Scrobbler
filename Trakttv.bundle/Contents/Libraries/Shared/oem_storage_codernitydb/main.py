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

        try:
            self.database.insert(item)
            return True
        except Exception, ex:
            log.warn('Unable to update collection: %s', ex, exc_info=True)

        return False

    #
    # Index methods
    #

    @Elapsed.track
    def update_index(self, source, target, response):
        data = self.format.decode(
            ModelRegistry['Index'],
            self.format.load_file(response.raw),
            children=False
        )

        for key, item in data.get('items', {}).items():
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

            # Store metadata in database
            self.database.insert(item)

        return True

    #
    # Item methods
    #

    def has_item(self, source, target, key):
        try:
            self.database.get('item_key', (source, target, key))
            return True
        except RecordNotFound:
            pass

        return False

    @Elapsed.track
    def update_item(self, source, target, key, response, metadata):
        item = self.format.decode(
            ModelRegistry['Item'],
            self.format.load_file(response.raw),
            media=metadata.media
        )

        # Set attributes
        item['_'] = {
            't': 'item',
            'k': key,

            'c': {
                's': source,
                't': target
            }
        }

        # Store metadata in database
        self.database.insert(item)
        return True
