from plugin.core.constants import PLUGIN_VERSION_BASE, PLUGIN_VERSION_BRANCH
from plugin.core.helpers.error import ErrorHasher
from plugin.core.logger.filters import DuplicateReportFilter, ExceptionReportFilter, RequestsReportFilter, TraktReportFilter
from plugin.core.logger.filters.events import EventsReportFilter

from raven import Client
from raven.handlers.logging import SentryHandler, RESERVED
from raven.utils import six
from raven.utils.stacks import iter_stack_frames, label_from_frame
import datetime
import logging
import os
import platform
import re
import sys

log = logging.getLogger(__name__)


VERSION = '.'.join([str(x) for x in PLUGIN_VERSION_BASE])

RE_BUNDLE_PATH = re.compile(r"^.*?(?P<path>\w+\.bundle(?:\\|\/).*?)$", re.IGNORECASE)
RE_TRACEBACK_HEADER = re.compile(r"^Exception (.*?)\(most recent call last\)(.*?)$", re.IGNORECASE | re.DOTALL)

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
        'urllib2'
    ],

    # Plugin + System details
    'release': VERSION,
    'tags': {
        # Plugin
        'plugin.version': VERSION,
        'plugin.branch': PLUGIN_VERSION_BRANCH,

        # System
        'os.system': platform.system(),
        'os.release': platform.release(),
        'os.version': platform.version()
    }
}


class ErrorReporter(Client):
    server = 'sentry.skipthe.net'
    key = '51814d6692f142ad88393d90a606643a:02374118037e4908a0dc627fcba3e613'
    project = 1

    def __init__(self, dsn=None, raise_send_errors=False, **options):
        # Build URI
        if dsn is None:
            dsn = self.build_dsn()

        # Construct raven client
        super(ErrorReporter, self).__init__(dsn, raise_send_errors, **options)

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


class ErrorReporterHandler(SentryHandler):
    def _emit(self, record, **kwargs):
        data = {
            'user': {'id': self.client.name}
        }

        extra = getattr(record, 'data', None)
        if not isinstance(extra, dict):
            if extra:
                extra = {'data': extra}
            else:
                extra = {}

        for k, v in six.iteritems(vars(record)):
            if k in RESERVED:
                continue
            if k.startswith('_'):
                continue
            if '.' not in k and k not in ('culprit', 'server_name'):
                extra[k] = v
            else:
                data[k] = v

        stack = getattr(record, 'stack', None)
        if stack is True:
            stack = iter_stack_frames()

        if stack:
            stack = self._get_targetted_stack(stack, record)

        date = datetime.datetime.utcfromtimestamp(record.created)
        event_type = 'raven.events.Message'
        handler_kwargs = {
            'params': record.args,
        }
        try:
            handler_kwargs['message'] = six.text_type(record.msg)
        except UnicodeDecodeError:
            # Handle binary strings where it should be unicode...
            handler_kwargs['message'] = repr(record.msg)[1:-1]

        try:
            handler_kwargs['formatted'] = six.text_type(record.message)
        except UnicodeDecodeError:
            # Handle binary strings where it should be unicode...
            handler_kwargs['formatted'] = repr(record.message)[1:-1]

        # If there's no exception being processed, exc_info may be a 3-tuple of None
        # http://docs.python.org/library/sys.html#sys.exc_info
        try:
            exc_info = self._exc_info(record)
        except Exception, ex:
            log.info('Unable to retrieve exception info - %s', ex, exc_info=True)
            exc_info = None

        exception_hash = None

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
            culprit = label_from_frame({'module': record.name, 'function': record.funcName})
            if culprit:
                data['culprit'] = culprit

        data['level'] = record.levelno
        data['logger'] = record.name

        # Store record `tags` in message
        if hasattr(record, 'tags'):
            kwargs['tags'] = record.tags

        if exception_hash:
            # Store `exception_hash` in message
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

        if not hasattr(ex, 'message'):
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
        except Exception, ex:
            log.info('Unable to retrieve traceback culprit - %s', ex, exc_info=True)
            culprit = None

        if culprit and len(culprit) == 3:
            file_path, _, function_name = culprit

            if function_name != '<module>':
                return 'Exception raised in %s(): %s' % (function_name, ex)

            # Build module name from path
            try:
                module = cls._module_name(file_path)
            except Exception, ex:
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


# Build client
RAVEN = ErrorReporter(**PARAMS)

# Construct logging handler
ERROR_REPORTER_HANDLER = ErrorReporterHandler(RAVEN, level=logging.WARNING)

ERROR_REPORTER_HANDLER.filters = [
    DuplicateReportFilter(),
    EventsReportFilter(),
    ExceptionReportFilter(),
    RequestsReportFilter(),
    TraktReportFilter()
]
