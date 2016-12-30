from plugin.core.constants import PLUGIN_VERSION, PLUGIN_VERSION_BASE, PLUGIN_VERSION_BRANCH
from plugin.core.helpers.error import ErrorHasher
from plugin.core.helpers.variable import merge
from plugin.core.libraries.helpers.system import SystemHelper
from plugin.core.logger.filters import DuplicateReportFilter, ExceptionReportFilter, FrameworkFilter,\
    RequestsReportFilter, TraktReportFilter, TraktNetworkFilter
from plugin.core.logger.filters.events import EventsReportFilter

from raven import Client, breadcrumbs
from raven._compat import string_types, text_type
from raven.handlers.logging import SentryHandler, extract_extra
from raven.utils.stacks import iter_stack_frames
import datetime
import logging
import os
import raven
import re
import sys

log = logging.getLogger(__name__)


VERSION = '.'.join([str(x) for x in PLUGIN_VERSION_BASE])

RE_BUNDLE_PATH = re.compile(r"^.*?(?P<path>\w+\.bundle(?:\\|\/).*?)$", re.IGNORECASE)
RE_TRACEBACK_HEADER = re.compile(r"^Exception (.*?)\(most recent call last\)(.*?)$", re.IGNORECASE | re.DOTALL)

ENVIRONMENTS = {
    'master': 'production',
    'beta': 'beta'
}

PARAMS = {
    # Message processors + filters
    'processors': [
        'raven.processors.RemoveStackLocalsProcessor',
        'plugin.raven.processors.RelativePathProcessor'
    ],

    'exclude_paths': [
        'Framework.api',
        'Framework.code',
        'Framework.components',
        'Framework.core',
        'urllib2'
    ],

    # Release details
    'release': PLUGIN_VERSION,
    'environment': ENVIRONMENTS.get(PLUGIN_VERSION_BRANCH, 'development'),

    # Tags
    'tags': merge(SystemHelper.attributes(), {
        'plugin.version': VERSION,
        'plugin.branch': PLUGIN_VERSION_BRANCH
    })
}

# Configure raven breadcrumbs
breadcrumbs.ignore_logger('plugin.core.logger.handlers.error_reporter.ErrorReporter')
breadcrumbs.ignore_logger('peewee')


class ErrorReporterClient(Client):
    server = 'sentry.skipthe.net'

    def __init__(self, project, key, raise_send_errors=False, **kwargs):
        self.project = project
        self.key = key

        # Construct raven client
        super(ErrorReporterClient, self).__init__(self.build_dsn(), raise_send_errors, **kwargs)

    def build_dsn(self, protocol='threaded+requests+http'):
        return '%s://%s@%s/%s' % (
            protocol,
            self.key,
            self.server,
            self.project
        )

    def set_protocol(self, protocol):
        # Build new DSN URI
        dsn = self.build_dsn(protocol)

        # Update client DSN
        self.set_dsn(dsn)

    def send_remote(self, url, data, headers=None):
        if headers is None:
            headers = {}

        # Update user agent
        headers['User-Agent'] = 'raven-python/%s tfp/%s-%s' % (
            # Raven
            raven.VERSION,

            # Trakt.tv (for Plex)
            VERSION,
            PLUGIN_VERSION_BRANCH
        )

        # Send event
        super(ErrorReporterClient, self).send_remote(url, data, headers)


class ErrorReporterHandler(SentryHandler):
    def _emit(self, record, **kwargs):
        data, extra = extract_extra(record)

        # Use client name as default user id
        data.setdefault('user', {'id': self.client.name})

        # Retrieve stack
        stack = getattr(record, 'stack', None)
        if stack is True:
            stack = iter_stack_frames()

        if stack:
            stack = self._get_targetted_stack(stack, record)

        # Build message
        date = datetime.datetime.utcfromtimestamp(record.created)
        event_type = 'raven.events.Message'
        handler_kwargs = {
            'params': record.args,
        }

        try:
            handler_kwargs['message'] = text_type(record.msg)
        except UnicodeDecodeError:
            # Handle binary strings where it should be unicode...
            handler_kwargs['message'] = repr(record.msg)[1:-1]

        try:
            handler_kwargs['formatted'] = text_type(record.message)
        except UnicodeDecodeError:
            # Handle binary strings where it should be unicode...
            handler_kwargs['formatted'] = repr(record.message)[1:-1]

        # Retrieve exception information from record
        try:
            exc_info = self._exc_info(record)
        except Exception as ex:
            log.info('Unable to retrieve exception info - %s', ex, exc_info=True)
            exc_info = None

        # Parse exception information
        exception_hash = None

        # If there's no exception being processed, exc_info may be a 3-tuple of None
        # http://docs.python.org/library/sys.html#sys.exc_info
        if exc_info and len(exc_info) == 3 and all(exc_info):
            message = handler_kwargs.get('formatted')

            # Replace exception messages with more helpful details
            if not record.exc_info and message and RE_TRACEBACK_HEADER.match(message):
                # Generate new record title
                handler_kwargs['formatted'] = '%s\n\n%s' % (
                    self._generate_title(record, exc_info),
                    message
                )
            elif not record.exc_info:
                log.debug("Message %r doesn't match traceback header", message)

            # capture the standard message first so that we ensure
            # the event is recorded as an exception, in addition to having our
            # message interface attached
            handler = self.client.get_handler(event_type)
            data.update(handler.capture(**handler_kwargs))

            event_type = 'raven.events.Exception'
            handler_kwargs = {'exc_info': exc_info}

            # Calculate exception hash
            exception_hash = ErrorHasher.hash(exc_info=exc_info)

        # HACK: discover a culprit when we normally couldn't
        elif not (data.get('stacktrace') or data.get('culprit')) and (record.name or record.funcName):
            culprit = self._label_from_frame({'module': record.name, 'function': record.funcName})

            if culprit:
                data['culprit'] = culprit

        data['level'] = record.levelno
        data['logger'] = record.name

        # Store record `tags` in message
        if hasattr(record, 'tags'):
            kwargs['tags'] = record.tags
        elif self.tags:
            kwargs['tags'] = self.tags

        # Store `exception_hash` in message (if defined)
        if exception_hash:
            if 'tags' not in kwargs:
                kwargs['tags'] = {}

            kwargs['tags']['exception.hash'] = exception_hash

        kwargs.update(handler_kwargs)

        return self.client.capture(
            event_type, stack=stack, data=data,
            extra=extra, date=date, **kwargs
        )

    @classmethod
    def _exc_info(cls, record):
        if record.exc_info and all(record.exc_info):
            return record.exc_info

        # Determine if record is a formatted exception
        message = record.getMessage()

        if message and message.lower().startswith('exception'):
            return cls._extract_exc_info(record)

        return None

    @staticmethod
    def _extract_exc_info(record):
        # Retrieve last exception information
        exc_info = sys.exc_info()

        # Ensure exception information is valid
        if not exc_info or len(exc_info) != 3 or not all(exc_info):
            return None

        # Retrieve exception
        _, ex, _ = exc_info

        if not hasattr(ex, 'message') or not isinstance(ex.message, string_types):
            return None

        # Retrieve last line of log record
        lines = record.message.strip().split('\n')
        last_line = lines[-1].lower()

        # Ensure exception message matches last line of record message
        message = ex.message.lower()

        if message not in last_line:
            log.debug("Ignored exception with message %r, doesn't match line: %r", message, last_line)
            return None

        return exc_info

    @classmethod
    def _traceback_culprit(cls, tb):
        result = None

        found_bundle = False

        while tb is not None:
            frame = tb.tb_frame
            line_num = tb.tb_lineno

            code = frame.f_code
            path = code.co_filename
            function_name = code.co_name

            # Retrieve bundle path
            bundle_path = cls.match_bundle(path)

            if bundle_path and bundle_path.startswith('trakttv.bundle'):
                # Found trace matching the current bundle
                found_bundle = True
            elif found_bundle:
                # Use previous trace matching current bundle
                break

            # Check if there is another trace available
            if tb.tb_next is None:
                # No traces left, use current trace
                result = (path, line_num, function_name)
                break

            # Store current culprit
            result = (path, line_num, function_name)

            # Move to next trace
            tb = tb.tb_next

        # Return "best" culprit match
        return result

    @staticmethod
    def match_bundle(path):
        path = path.lower().replace('\\', '/')
        match = RE_BUNDLE_PATH.match(path)

        if match:
            return match.group('path')

        return None

    @classmethod
    def _generate_title(cls, record, exc_info):
        _, ex, tb = exc_info

        # Try retrieve culprit from traceback
        try:
            culprit = cls._traceback_culprit(tb)
        except Exception as ex:
            log.info('Unable to retrieve traceback culprit - %s', ex, exc_info=True)
            culprit = None

        if culprit and len(culprit) == 3:
            file_path, _, function_name = culprit

            if function_name != '<module>':
                return 'Exception raised in %s(): %s' % (function_name, ex)

            # Build module name from path
            try:
                module = cls._module_name(file_path)
            except Exception as ex:
                log.info('Unable to retrieve module name - %s', ex, exc_info=True)
                module = None

            if not module:
                return 'Exception raised in <unknown>'

            return 'Exception raised in %s: %s' % (module, ex)

        # Try retrieve culprit from log record
        if record.funcName:
            return 'Exception raised in %s()' % (
                record.funcName
            )

        log.debug('Unable to generate title for record %r, exc_info: %r', record, exc_info)
        return 'Exception raised in <unknown>'

    @staticmethod
    def _module_name(file_path):
        # Convert to relative path
        path = file_path.lower()
        path = path[path.index('trakttv.bundle'):]
        path = os.path.splitext(path)[0]

        # Split path into fragments
        fragments = path.split(os.sep)[2:]

        if not fragments or fragments[0] not in ['code', 'libraries']:
            return None

        # Build module name
        module = None

        if fragments[0] == 'code':
            module = '.'.join(fragments)
        elif fragments[0] == 'libraries':
            module = '.'.join(fragments[2:])

        # Verify module name was built
        if not module:
            return None

        return module

    @staticmethod
    def _label_from_frame(frame):
        module = frame.get('module') or '?'
        function = frame.get('function') or '?'

        if module == function == '?':
            return ''

        return '%s in %s' % (module, function)


class ErrorReporter(object):
    plugin = ErrorReporterClient(
        project=1,
        key='9297cd482d974cc983eaa11665662082:1452d96d3b794ef0914e2b20d7a590b5',
        **PARAMS
    )

    trakt = ErrorReporterClient(
        project=8,
        key='904ebc3f0c2642aea78c341c7cefbbb6:3fac822481004f8e8e41b56261056a31',
        enable_breadcrumbs=False,
        **PARAMS
    )

    @classmethod
    def construct_handler(cls, client, filters, level=logging.WARNING):
        handler = ErrorReporterHandler(client, level=level)
        handler.filters = filters
        return handler

    @classmethod
    def set_name(cls, name):
        cls.plugin.name = name
        cls.trakt.name = name

    @classmethod
    def set_protocol(cls, protocol):
        cls.plugin.set_protocol(protocol)
        cls.trakt.set_protocol(protocol)

    @classmethod
    def set_tags(cls, *args, **kwargs):
        # Update clients with dictionary arguments
        for value in args:
            if type(value) is dict:
                cls.plugin.tags.update(value)
                cls.trakt.tags.update(value)
            else:
                raise ValueError('Only dictionaries can be provided as arguments, found: %s' % type(value))

        # Update clients with `kwargs` tags
        cls.plugin.tags.update(kwargs)
        cls.trakt.tags.update(kwargs)


# Construct logging handlers
PLUGIN_REPORTER_HANDLER = ErrorReporter.construct_handler(ErrorReporter.plugin, [
    FrameworkFilter('filter'),
    TraktNetworkFilter(),

    DuplicateReportFilter(),
    EventsReportFilter(),
    ExceptionReportFilter(),
    RequestsReportFilter(),
    TraktReportFilter()
])

TRAKT_REPORTER_HANDLER = ErrorReporter.construct_handler(ErrorReporter.trakt, [
    TraktNetworkFilter(mode='include')
])
