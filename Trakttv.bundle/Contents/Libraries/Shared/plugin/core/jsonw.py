import logging

log = logging.getLogger(__name__)


def json_import():
    try:
        import simplejson as json

        log.info("Using 'simplejson' module for JSON serialization")
        return json, 'json'
    except ImportError:
        pass

    # Try fallback to 'json' module
    try:
        import json

        log.info("Using 'json' module for JSON serialization")
        return json, 'json'
    except ImportError:
        pass


# Import json serialization module
JSON, JSON_MODULE = json_import()


# JSON serialization wrappers to simplejson/json or demjson
def json_decode(s):
    if JSON_MODULE == 'json':
        return JSON.loads(s)

    raise NotImplementedError()


def json_encode(obj):
    if JSON_MODULE == 'json':
        return JSON.dumps(obj)

    raise NotImplementedError()


def json_write(path, obj, cls=None):
    if JSON_MODULE == 'json':
        with open(path, 'wb') as fp:
            return JSON.dump(obj, fp, cls=cls)

    raise NotImplementedError()


class DictionaryTransformer(object):
    def __init__(self, dictionary):
        self.dictionary = dictionary

    def iteritems(self):
        for key, value in self.dictionary.iteritems():
            yield self.transform(key, value)

    def items(self):
        return self.iteritems()

    def transform(self, key, value):
        return key, value

    def _asdict(self):
        return self


class ArtifactTransformer(DictionaryTransformer):
    def transform(self, key, value):
        return str(key), value


class ArtifactEncoder(JSON.JSONEncoder):
    def default(self, o):
        return repr(o)
