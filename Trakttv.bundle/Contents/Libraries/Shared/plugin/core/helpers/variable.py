from plugin.core.environment import Environment

import collections
import re
import unicodedata


def flatten(text):
    if text is None:
        return None

    # Normalize `text` to ascii
    text = normalize(text)

    # Remove special characters
    text = re.sub('[^A-Za-z0-9\s]+', '', text)

    # Merge duplicate spaces
    text = ' '.join(text.split())

    # Convert to lower-case
    return text.lower()


def get_pref(key, default=None):
    if Environment.dict['preferences'] and key in Environment.dict['preferences']:
        return Environment.dict['preferences'][key]

    return Environment.prefs[key] or default


def merge(a, b, recursive=False):
    if not recursive:
        a.update(b)
        return a

    # Merge child dictionaries
    for k, v in b.iteritems():
        if isinstance(v, collections.Mapping):
            r = merge(a.get(k, {}), v, recursive=True)
            a[k] = r
        else:
            a[k] = b[k]

    return a


def normalize(text):
    if text is None:
        return None

    # Normalize unicode characters
    if type(text) is unicode:
        text = unicodedata.normalize('NFKD', text)

    # Ensure text is ASCII, ignore unknown characters
    return text.encode('ascii', 'ignore')


def resolve(value, *args, **kwargs):
    if hasattr(value, '__call__'):
        return value(*args, **kwargs)

    return value


def to_integer(value):
    if value is None:
        return None

    try:
        return int(value)
    except:
        return None


def to_tuple(value):
    if type(value) is tuple:
        return value

    return value,


def try_convert(value, value_type, default=None):
    try:
        return value_type(value)
    except ValueError:
        return default
    except TypeError:
        return default
