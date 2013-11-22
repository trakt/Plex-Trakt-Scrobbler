from lxml import etree
import urllib2
import socket
import json
import time


HTTP_RETRY_CODES = [408, 500, (502, 504), 522, 524, (598, 599)]


def request(url, response_type='text', data=None, data_type='application/octet-stream', retry=False,
            timeout=None, max_retries=3, retry_sleep=5, **kwargs):
    """Send an HTTP Request

    :param url: Request url
    :type url: str

    :param response_type: Expected response data type
    :type response_type: str

    :param data: Data to send in the request
    :type data: str or dict

    :param data_type: Type of data to send in the request
    :type data_type: str

    :param retry: Should the request be retried on errors?
    :type retry: bool

    :param timeout: Request timeout seconds
    :type timeout: int

    :param max_retries: Number of retries before we give up on the request
    :type max_retries: int

    :param retry_sleep: Number of seconds to sleep for between requests
    :type retry_sleep: int


    :rtype: Response
    """
    req = urllib2.Request(url)

    # Add request body
    if data:
        # Convert request data
        if data_type == 'json' and type(data) is not str:
            data = json.dumps(data)

        if type(data) is not str:
            raise ValueError("Request data is not in a valid format, type(data) = %s, data_type = \"%s\"" % (
                type(data), data_type)
            )

        req.data = data
        req.add_header('Content-Length', len(data))

        if data_type == 'json':
            req.add_header('Content-Type', 'application/json')
        else:
            req.add_header('Content-Type', data_type)

    # Write request debug entry to log
    internal_log_request(url, response_type, data, data_type, retry, timeout)

    if timeout:
        kwargs['timeout'] = timeout

    return internal_retry(
        req,

        retry=retry,
        max_retries=max_retries,
        retry_sleep=retry_sleep,

        response_type=response_type,
        **kwargs
    )


def internal_log_request(url, response_type, data, data_type, retry, timeout):
    debug_values = [
        "len(data): %s, data_type: '%s'" % (
            len(data) if data else None,
            data_type
        ) if data else '',

        'retry' if retry else None,

        ('timeout: %s' % timeout) if timeout else None
    ]

    # Filter empty values
    debug_values = [x for x in debug_values if x]

    Log.Debug("Requesting '%s' (%s) %s" % (
        url,
        response_type,

        ('[%s]' % ', '.join(debug_values)) if len(debug_values) else ''
    ))


def internal_retry(req, retry=False, max_retries=3, retry_sleep=5, **kwargs):
    if not retry:
        return internal_request(req, **kwargs)

    kwargs['raise_exceptions'] = True

    response = None
    retry_num = 0

    while response is None and retry_num < max_retries:
        if retry_num > 0:
            Log.Debug('Waiting %ss before retrying request' % retry_sleep)
            time.sleep(retry_sleep)

            Log.Debug('Retrying request, try #%s' % retry_num)

        try:
            response = internal_request(req, **kwargs)
        except NetworkError, e:
            Log.Debug('Request returned a network error: (%s) %s' % (e.code, e))

            # If this is possibly a client error, stop retrying and just return
            if not should_retry(e.code):
                Log.Debug('Request error code %s is possibly client related, not retrying the request', e.code)
                return None

        except RequestError, e:
            Log.Debug('Request returned exception: %s' % e)
            response = None

        retry_num += 1

    return response


def internal_request(req, response_type='text', raise_exceptions=False, default=None, **kwargs):
    try:
        resp = urllib2.urlopen(req, **kwargs)
        return Response.from_urllib(response_type, resp)
    except RequestError, e:
        ex = e
    except Exception, e:
        ex = NetworkError.from_exception(e)

    if raise_exceptions:
        raise ex
    else:
        Log.Warn('Network request raised exception: %s' % ex)

    return default


def should_retry(error_code):
    # If there is no error code, assume we should retry
    if error_code is None:
        return True

    for retry_code in HTTP_RETRY_CODES:
        if type(retry_code) is tuple and len(retry_code) == 2:
            if retry_code[0] <= error_code <= retry_code[1]:
                return True
        elif type(retry_code) is int:
            if retry_code == error_code:
                return True
        else:
            raise ValueError("Invalid retry_code specified: %s" % retry_code)

    return False


class Response(object):
    def __init__(self, data, response):
        self.data = data

        self.inner_response = response

    @classmethod
    def from_urllib(cls, response_type, response):
        return Response(
            cls.parse_data(response_type, response.read()),
            response
        )

    @classmethod
    def parse_data(cls, response_type, data):
        if response_type == 'text':
            return data
        elif response_type == 'json':
            return cls.parse_json(data)
        elif response_type == 'xml':
            return cls.parse_xml(data)
        else:
            raise RequestError("Unknown response type provided")

    @classmethod
    def parse_json(cls, data):
        try:
            return json.loads(data)
        except Exception, e:
            raise ParseError.from_exception(e)

    @classmethod
    def parse_xml(cls, data):
        try:
            return etree.fromstring(data)
        except Exception, e:
            raise ParseError.from_exception(e)


class RequestError(Exception):
    def __init__(self, message, inner_exception=None):
        self.message = message
        self.inner_exception = inner_exception

    def __str__(self):
        ex_class = getattr(self.inner_exception, '__class__') if self.inner_exception else None

        if self.inner_exception:
            ex_class = getattr(ex_class, '__name__')

        return '<NetworkError%s "%s">' % (
            (' (%s)' % ex_class) if ex_class else '',
            self.message
        )


class NetworkError(RequestError):
    def __init__(self, message, code, inner_exception=None):
        super(NetworkError, self).__init__(message, inner_exception)

        self.code = code

    @classmethod
    def from_exception(cls, e):
        code = None

        if type(e) is urllib2.HTTPError:
            code = e.code

        if type(e) is socket.timeout:
            code = 408

        return NetworkError(e.message or str(e), code, e)


class ParseError(RequestError):
    @classmethod
    def from_exception(cls, e):
        return ParseError(e.message or str(e), e)
