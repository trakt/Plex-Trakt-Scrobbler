from CodernityDB.tree_index import TreeBasedIndex, MultiTreeBasedIndex
from hashlib import md5


class CollectionKeyIndex(TreeBasedIndex):
    _version = 1

    def __init__(self, *args, **kwargs):
        kwargs['key_format'] = '32s'
        super(CollectionKeyIndex, self).__init__(*args, **kwargs)

    def make_key(self, (source, target)):
        return md5(' '.join([str(source), str(target)])).hexdigest()

    def make_key_value(self, data):
        attributes = data.get('_', {})
        collection = attributes.get('c', {})

        if attributes.get('t') != 'collection':
            return

        if not collection.get('s') or not collection.get('t'):
            return

        return self.make_key((
            collection['s'],
            collection['t']
        )), None

class MetadataKeyIndex(MultiTreeBasedIndex):
    _version = 1

    custom_header = """from CodernityDB.tree_index import MultiTreeBasedIndex"""

    def __init__(self, *args, **kwargs):
        kwargs['key_format'] = '32s'
        super(MetadataKeyIndex, self).__init__(*args, **kwargs)

    def make_key(self, (source, target, key)):
        return md5(' '.join([str(source), str(target), str(key)])).hexdigest()

    def make_key_value(self, data):
        attributes = data.get('_', {})
        collection = attributes.get('c', {})

        if attributes.get('t') != 'metadata' or not attributes.get('k'):
            return

        if not collection.get('s') or not collection.get('t'):
            return

        return self.make_key((
            collection['s'],
            collection['t'],
            attributes['k']
        )), None


class MetadataCollectionIndex(TreeBasedIndex):
    _version = 1

    def __init__(self, *args, **kwargs):
        kwargs['key_format'] = '32s'
        super(MetadataCollectionIndex, self).__init__(*args, **kwargs)

    def make_key(self, (source, target)):
        return md5(' '.join([str(source), str(target)])).hexdigest()

    def make_key_value(self, data):
        attributes = data.get('_', {})
        collection = attributes.get('c', {})

        if attributes.get('t') != 'metadata':
            return

        if not collection.get('s') or not collection.get('t'):
            return

        return self.make_key((
            collection['s'],
            collection['t']
        )), None


class ItemKeyIndex(TreeBasedIndex):
    _version = 1

    def __init__(self, *args, **kwargs):
        kwargs['key_format'] = '32s'
        super(ItemKeyIndex, self).__init__(*args, **kwargs)

    def make_key(self, (source, target, key)):
        return md5(' '.join([str(source), str(target), str(key)])).hexdigest()

    def make_key_value(self, data):
        attributes = data.get('_', {})
        collection = attributes.get('c', {})

        if attributes.get('t') != 'item' or not attributes.get('k'):
            return

        if not collection.get('s') or not collection.get('t'):
            return

        return self.make_key((
            collection['s'],
            collection['t'],
            attributes['k']
        )), None
