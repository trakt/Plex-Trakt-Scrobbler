from plugin.core.constants import PLUGIN_VERSION_BASE, PLUGIN_VERSION_BRANCH
from plugin.core.helpers.error import ErrorHasher
from plugin.core.logger.filters import RequestsReportFilter

from raven import Client
from raven.handlers.logging import SentryHandler, RESERVED
from raven.utils import six
from raven.utils.stacks import iter_stack_frames, label_from_frame
import datetime
import logging
import platform

log = logging.getLogger(__name__)


VERSION = '.'.join([str(x) for x in PLUGIN_VERSION_BASE])

PARAMS = {
    # Message processors + filters
    'processors': [
        'raven.processors.RemoveStackLocalsProcessor',
        'plugin.raven.processors.RelativePathProcessor'
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
    key = 'e043ce2ca140486d9104b8c6164f1a82:d01d4eabb8aa4aacbd6bb61a36f92033'
    project = 1

    def __init__(self, dsn=None, raise_send_errors=False, **options):
        # Build URI
        if dsn is None:
            dsn = self.build_dsn()

        # Construct raven client
        super(ErrorReporter, self).__init__(dsn, raise_send_errors, **options)

    def build_dsn(self, protocol='requests+http'):
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
        exception_hash = None

        if record.exc_info and all(record.exc_info):
            # capture the standard message first so that we ensure
            # the event is recorded as an exception, in addition to having our
            # message interface attached
            handler = self.client.get_handler(event_type)
            data.update(handler.capture(**handler_kwargs))

            event_type = 'raven.events.Exception'
            handler_kwargs = {'exc_info': record.exc_info}

            # Calculate exception hash
            exception_hash = ErrorHasher.hash(exc_info=record.exc_info)

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


# Build client
RAVEN = ErrorReporter(**PARAMS)

# Construct logging handler
ERROR_REPORTER_HANDLER = ErrorReporterHandler(RAVEN, level=logging.WARNING)
ERROR_REPORTER_HANDLER.addFilter(RequestsReportFilter())
