import threading
import time
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


def parse_section(section):
    return (
        section.get('type', None),
        section.get('key', None),
        section.get('title', None)
    )


def itersections(sections, types=('show', 'movie')):
    """Iterate over valid PMS sections of type 'show' or 'movie'"""
    result = []

    for section in [parse_section(s) for s in sections]:
        # Ensure fields exist
        if all(v is not None for v in section):
            section_type, key, title = section
            # Ensure section is of type 'show' or 'movie'
            if section_type in types:
                result.append((section_type, key, title))

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


def str_format(s, *args, **kwargs):
    """Return a formatted version of S, using substitutions from args and kwargs.

    (Roughly matches the functionality of str.format but ensures compatibility with Python 2.5)
    """

    args = list(args)

    x = 0
    while x < len(s):
        # Skip non-start token characters
        if s[x] != '{':
            x += 1
            continue

        end_pos = s.find('}', x)

        # If end character can't be found, move to next character
        if end_pos == -1:
            x += 1
            continue

        name = s[x + 1:end_pos]

        # Ensure token name is alpha numeric
        if not name.isalnum():
            x += 1
            continue

        # Try find value for token
        value = args.pop(0) if args else kwargs.get(name)

        if value:
            value = str(value)

            # Replace token with value
            s = s[:x] + value + s[end_pos + 1:]

            # Update current position
            x = x + len(value) - 1

        x += 1

    return s


def str_pad(s, length, align='left', pad_char=' '):
    if not s:
        return s

    s = str(s)

    if len(s) == length:
        return s

    if align == 'left':
        if len(s) > length:
            return s[:length]
        else:
            return s + (pad_char * (length - len(s)))
    elif align == 'right':
        if len(s) > length:
            return s[len(s) - length:]
        else:
            return (pad_char * (length - len(s))) + s
    else:
        raise ValueError("Unknown align type, expected either 'left' or 'right'")


def total_seconds(span):
    return (span.microseconds + (span.seconds + span.days * 24 * 3600) * 1e6) / 1e6


def sum(values):
    result = 0

    for x in values:
        result = result + x

    return result


def timestamp():
    return int(time.time())


def apply_async(func, *args, **kwargs):
    def runnable():
        func(*args, **kwargs)

    thread = threading.Thread(target=runnable)
    thread.start()
