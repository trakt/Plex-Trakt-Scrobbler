import socket
import urllib
import urllib2


def request(url, data=None, response_type='text', timeout=None):
    if data and type(data) is not str:
        data = JSON.StringFromObject(data)

    parameters = {}
    if timeout:
        parameters['timeout'] = timeout

    Log.Debug("Requesting '%s'" % url)

    # Try get the response
    response = None

    try:
        req = urllib2.Request(url)

        if data:
            req.data = data
            req.add_header('Content-Length', '%d' % len(data))
            req.add_header('Content-Type', 'application/octet-stream')

        response = urllib2.urlopen(req, **parameters)
    except Exception, e:
        # Return a RequestError for known HTTP exceptions
        request_error = RequestError.from_exception(e)
        if request_error:
            raise request_error

        # If we caught an unknown exception, re-raise it
        raise e

    # Parse response content into specified response_type
    content = response.read()

    if response_type == 'json':
        try:
            return JSON.ObjectFromString(content)
        except:
            Log.Warn('JSON decoding failed, returning None')
            return None

    if response_type == 'text':
        return content

    raise ValueError('Unknown response_type specified, expecting "text" or "json"')


class RequestError(Exception):
    def __init__(self, inner_exception, message, code):
        self.inner_exception = inner_exception
        self.message = message
        self.code = code

    @staticmethod
    def from_exception(e):
        message = None
        code = None

        if type(e) is socket.timeout:
            code = 408
        elif type(e) is Ex.HTTPError:
            code = e.code
        elif type(e) is Ex.URLError:
            code, message = e.reason
        else:
            return None

        if not message and code:
            message = responses[code][1] if code in responses else 'Unknown Error'

        return RequestError(e, message, code)


responses = {
    100: ('Continue', 'Request received, please continue'),
    101: ('Switching Protocols',
          'Switching to new protocol; obey Upgrade header'),

    200: ('OK', 'Request fulfilled, document follows'),
    201: ('Created', 'Document created, URL follows'),
    202: ('Accepted',
          'Request accepted, processing continues off-line'),
    203: ('Non-Authoritative Information', 'Request fulfilled from cache'),
    204: ('No Content', 'Request fulfilled, nothing follows'),
    205: ('Reset Content', 'Clear input form for further input.'),
    206: ('Partial Content', 'Partial content follows.'),

    300: ('Multiple Choices',
          'Object has several resources -- see URI list'),
    301: ('Moved Permanently', 'Object moved permanently -- see URI list'),
    302: ('Found', 'Object moved temporarily -- see URI list'),
    303: ('See Other', 'Object moved -- see Method and URL list'),
    304: ('Not Modified',
          'Document has not changed since given time'),
    305: ('Use Proxy',
          'You must use proxy specified in Location to access this '
          'resource.'),
    307: ('Temporary Redirect',
          'Object moved temporarily -- see URI list'),

    400: ('Bad Request',
          'Bad request syntax or unsupported method'),
    401: ('Unauthorized',
          'Login failed'),
    402: ('Payment Required',
          'No payment -- see charging schemes'),
    403: ('Forbidden',
          'Request forbidden -- authorization will not help'),
    404: ('Not Found', 'Nothing matches the given URI'),
    405: ('Method Not Allowed',
          'Specified method is invalid for this server.'),
    406: ('Not Acceptable', 'URI not available in preferred format.'),
    407: ('Proxy Authentication Required', 'You must authenticate with '
                                           'this proxy before proceeding.'),
    408: ('Request Timeout', 'Request timed out; try again later.'),
    409: ('Conflict', 'Request conflict.'),
    410: ('Gone',
          'URI no longer exists and has been permanently removed.'),
    411: ('Length Required', 'Client must specify Content-Length.'),
    412: ('Precondition Failed', 'Precondition in headers is false.'),
    413: ('Request Entity Too Large', 'Entity is too large.'),
    414: ('Request-URI Too Long', 'URI is too long.'),
    415: ('Unsupported Media Type', 'Entity body in unsupported format.'),
    416: ('Requested Range Not Satisfiable',
          'Cannot satisfy request range.'),
    417: ('Expectation Failed',
          'Expect condition could not be satisfied.'),

    500: ('Internal Server Error', 'Server got itself in trouble'),
    501: ('Not Implemented',
          'Server does not support this operation'),
    502: ('Bad Gateway', 'Invalid responses from another server/proxy.'),
    503: ('Service Unavailable',
          'The server cannot process the request due to a high load'),
    504: ('Gateway Timeout',
          'The gateway server did not receive a timely response'),
    505: ('HTTP Version Not Supported', 'Cannot fulfill request.'),
}
