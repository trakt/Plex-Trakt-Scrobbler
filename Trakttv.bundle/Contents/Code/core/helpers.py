from core.logger import Logger

from plugin.core.constants import PLUGIN_PREFIX
from plugin.core.message import InterfaceMessages

import base64
import cerealizer
import functools
import hashlib
import inspect
import logging
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


def all(items):
    for item in items:
        if not item:
            return False
    return True


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

    # Construct thread
    th = threading.Thread(target=thread_wrapper, name=thread_name, kwargs={
        'func': func,
        'args': args,
        'kwargs': kwargs,
        'thread_name': thread_name
    })

    # Set daemon mode
    th.daemon = kwargs.pop('daemon', False)

    # Start thread
    try:
        th.start()
        log.debug("Spawned thread with name '%s'" % thread_name)
    except thread.error as ex:
        log.error('Unable to spawn thread: %s', ex, exc_info=True, extra={
            'data': {
                'active_count': threading.active_count()
            }
        })
        return None

    return th


def thread_wrapper(func, args=None, kwargs=None, thread_name=None):
    if args is None:
        args = ()

    if kwargs is None:
        kwargs = {}

    try:
        func(*args, **kwargs)
    except Exception as ex:
        log.error('Exception raised in thread "%s": %s', thread_name, ex, exc_info=True)


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

    try:
        request = Core.sandbox.context.request

        # Add request parameters (required for authentication on some clients)
        kwargs.update({
            # Client
            'X-Plex-Client-Identifier': request.headers.get('X-Plex-Client-Identifier'),
            'X-Plex-Product': request.headers.get('X-Plex-Product'),
            'X-Plex-Version': request.headers.get('X-Plex-Version'),

            # Platform
            'X-Plex-Platform': request.headers.get('X-Plex-Platform'),
            'X-Plex-Platform-Version': request.headers.get('X-Plex-Platform-Version'),

            # Device
            'X-Plex-Device': request.headers.get('X-Plex-Device'),
            'X-Plex-Device-Name': request.headers.get('X-Plex-Device-Name'),
            'X-Plex-Device-Screen-Resolution': request.headers.get('X-Plex-Device-Screen-Resolution'),

            # Authentication
            'X-Plex-Token': request.headers.get('X-Plex-Token')
        })

        # Retrieve protocol
        protocol = request.protocol

        if request.host.endswith('.plex.direct:32400'):
            # Assume secure connection
            protocol = 'https'

        # Prepend protocol and host (if not already in `location`)
        if request and request.host and location[0] == "/":
            location = protocol + "://" + request.host + location
    except Exception as ex:
        log.warn('Redirect - %s', str(ex), exc_info=True)

    # Append parameters
    if kwargs:
        location += '?' + urllib.urlencode([
            (key, value) for key, value in kwargs.items()
            if value is not None
        ])

    # Return redirect response
    return Redirect(location, True)


def catch_errors(func):
    @functools.wraps(func)
    def inner(*args, **kwargs):
        if InterfaceMessages.critical:
            return error_record_view(logging.CRITICAL, InterfaceMessages.record)

        try:
            return func(*args, **kwargs)
        except Exception as ex:
            if InterfaceMessages.critical:
                return error_record_view(logging.CRITICAL, InterfaceMessages.record)

            log.error('Exception raised in view: %s', ex, exc_info=True)

            return error_view(
                'Exception',
                ex.message
            )

    return inner


def error_record_view(level, record):
    # Retrieve level name
    if level == logging.CRITICAL:
        level_name = 'Critical Error'
    else:
        level_name = logging.getLevelName(level).capitalize()

    # Build error view
    if not record:
        return error_view(level_name)

    return error_view(
        level_name,
        record.message
    )


def error_view(title, message=None):
    oc = ObjectContainer(
        title2=title,
        no_cache=True
    )

    oc.add(DirectoryObject(
        key=PLUGIN_PREFIX,
        title=pad_title('%s: %s' % (
            title,
            message or 'Unknown'
        ))
    ))

    return oc
