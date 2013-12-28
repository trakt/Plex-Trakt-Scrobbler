import sys


PY25 = sys.version_info[0] == 2 and sys.version_info[1] == 5


def SyncDownString():

    if Prefs['sync_watched'] and Prefs['sync_ratings']:
        return "seen and rated"
    elif Prefs['sync_watched']:
        return "seen "
    elif Prefs['sync_ratings']:
        return "rated "
    else:
        return ""


def SyncUpString():
    action_strings = []
    if Prefs['sync_collection']:
        action_strings.append("library")
    if Prefs['sync_watched']:
        action_strings.append("seen items")
    if Prefs['sync_ratings']:
        action_strings.append("ratings")

    temp_string = ", ".join(action_strings)
    li = temp_string.rsplit(", ", 1)
    return " and ".join(li)


def is_number(s):
    try:
        float(s)
        return True
    except ValueError:
        return False
    except TypeError:
        return False


def try_convert(value, value_type):
    try:
        return value_type(value)
    except ValueError:
        return None
    except TypeError:
        return None


def add_attribute(target, source, key, value_type=str, func=None, target_key=None):
    if target_key is None:
        target_key = key

    value = try_convert(source.get(key, None), value_type)

    if value:
        target[target_key] = func(value) if func else value


def iterget(items, keys):
    result = []

    for item in items:
        values = [item]

        for key, value in [(key, item.get(key, None)) for key in keys]:
            values.append(value)

        result.append(values)

    return result


def finditems(subject, items, key):
    result = []

    for item in items:
        if key in item and item[key] == subject[key]:
            result.append(item)

    return result


def matches(subject, items, func):
    result = []

    for item in items:
        if func(item) == subject:
            result.append(item)

    return result


def extend(a, b=None):
    c = a.copy()

    if b is None:
        return c

    c.update(b)
    return c


def all(items):
    for item in items:
        if not item:
            return False
    return True


def json_import():
    try:
        import simplejson as json

        Log.Info("Using 'simplejson' module for JSON serialization")
        return json, 'json'
    except ImportError:
        pass

    # Try fallback to 'json' module
    try:
        import json

        Log.Info("Using 'json' module for JSON serialization")
        return json, 'json'
    except ImportError:
        pass

    # Try fallback to 'demjson' module
    try:
        import demjson

        Log.Info("Using 'demjson' module for JSON serialization")
        return demjson, 'demjson'
    except ImportError:
        Log.Warn("Unable to find json module for serialization")
        raise Exception("Unable to find json module for serialization")

# Import json serialization module
JSON, JSON_MODULE = json_import()


# JSON serialization wrappers to simplejson/json or demjson
def json_decode(s):
    if JSON_MODULE == 'json':
        return JSON.loads(s)

    if JSON_MODULE == 'demjson':
        return JSON.decode(s)

    raise NotImplementedError()


def json_encode(obj):
    if JSON_MODULE == 'json':
        return JSON.dumps(obj)

    if JSON_MODULE == 'demjson':
        return JSON.encode(obj)

    raise NotImplementedError()
