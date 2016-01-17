from core.logger import Logger

from plugin.core.constants import PLUGIN_PREFIX

import base64
import cerealizer
import hashlib
import inspect
import sys
import threading
import thread
import time
import urllib

log = Logger('core.helpers')


PY25 = sys.version_info[0] == 2 and sys.version_info[1] == 5


def try_convert(value, value_type, default=None):
    try:
        return value_type(value)
    except ValueError:
        return default
    except TypeError:
        return default


def add_attribute(target, source, key, value_type=str, func=None, target_key=None):
    if target_key is None:
        target_key = key

    value = try_convert(source.get(key, None), value_type)

    if value:
        target[target_key] = func(value) if func else value


def merge(a, b):
    a.update(b)
    return a


def all(items):
    for item in items:
        if not item:
            return False
    return True


def any(items):
    for item in items:
        if item:
            return True

    return False


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

    # Try fallback to 'demjson' module
    try:
        import demjson

        log.info("Using 'demjson' module for JSON serialization")
        return demjson, 'demjson'
    except ImportError:
        log.warn("Unable to find json module for serialization")
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


def str_pad(s, length, align='left', pad_char=' ', trim=False):
    if not s:
        return s

    if not isinstance(s, (str, unicode)):
        s = str(s)

    if len(s) == length:
        return s
    elif len(s) > length and not trim:
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


def pad_title(value):
    """Pad a title to 30 characters to force the 'details' view."""
    return str_pad(value, 30, pad_char=' ')


def total_seconds(span):
    return (span.microseconds + (span.seconds + span.days * 24 * 3600) * 1e6) / 1e6


def sum(values):
    result = 0

    for x in values:
        result = result + x

    return result


def timestamp():
    return str(time.time())


# <bound method type.start of <class 'Scrobbler'>>
RE_BOUND_METHOD = Regex(r"<bound method (type\.)?(?P<name>.*?) of <(class '(?P<class>.*?)')?")


def get_func_name(obj):
    if inspect.ismethod(obj):
        match = RE_BOUND_METHOD.match(repr(obj))

        if match:
            cls = match.group('class')
            if not cls:
                return match.group('name')

            return '%s.%s' % (
                match.group('class'),
                match.group('name')
            )

    return None


def get_class_name(cls):
    if not inspect.isclass(cls):
        cls = getattr(cls, '__class__')

    return getattr(cls, '__name__')


def spawn(func, *args, **kwargs):
    thread_name = kwargs.pop('thread_name', None) or get_func_name(func)

    def wrapper(thread_name, args, kwargs):
        try:
            func(*args, **kwargs)
        except Exception, ex:
            log.error('Thread "%s" raised an exception: %s', thread_name, ex, exc_info=True)

    th = threading.Thread(target=wrapper, name=thread_name, args=(thread_name, args, kwargs))

    try:
        th.start()
        log.debug("Spawned thread with name '%s'" % thread_name)
    except thread.error, ex:
        log.error('Unable to spawn thread: %s', ex, exc_info=True, extra={
            'data': {
                'active_count': threading.active_count()
            }
        })
        return None

    return th


def schedule(func, seconds, *args, **kwargs):
    def schedule_sleep():
        time.sleep(seconds)
        func(*args, **kwargs)

    spawn(schedule_sleep)


def build_repr(obj, keys):
    key_part = ', '.join([
        ('%s: %s' % (key, repr(getattr(obj, key))))
        for key in keys
    ])

    cls = getattr(obj, '__class__')

    return '<%s %s>' % (getattr(cls, '__name__'), key_part)


def plural(value):
    if type(value) is list:
        value = len(value)

    if value == 1:
        return ''

    return 's'


def join_attributes(**kwargs):
    fragments = [
        (('%s: %s' % (key, value)) if value else None)
        for (key, value) in kwargs.items()
    ]

    return ', '.join([x for x in fragments if x])


def md5(value):
    # Generate MD5 hash of key
    m = hashlib.md5()
    m.update(value)

    return m.hexdigest()


def safe_encode(string):
    string = str(string)
    return base64.b64encode(string).replace('/', '@').replace('+', '*').replace('=', '_')


def pack(obj):
    serialized_obj = cerealizer.dumps(obj)
    encoded_string = safe_encode(serialized_obj)
    return urllib.quote(encoded_string)


def function_path(name, ext=None, **kwargs):
    return '%s/:/function/%s%s?%s' % (
        PLUGIN_PREFIX,
        name,
        ('.%s' % ext) if ext else '',

        urllib.urlencode({
            'function_args': pack(kwargs)
        })
    )


def redirect(path, **kwargs):
    location = PLUGIN_PREFIX + path

    if kwargs:
        location += '?' + urllib.urlencode(kwargs)

    try:
        request = Core.sandbox.context.request

        # Retrieve protocol
        protocol = request.protocol

        if request.host.endswith('.plex.direct:32400'):
            # Secure connection
            protocol = 'https'

        # Build URL
        if request and request.host and location[0] == "/":
            location = protocol + "://" + request.host + location
    except Exception, ex:
        log.warn('Redirect - %s', str(ex), exc_info=True)

    # Return redirect response
    return Redirect(location)
