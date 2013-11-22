from lxml import etree
import urllib2
import json


def request(url, response_type='text', data=None, data_type='application/octet-stream', **kwargs):
    """Send an HTTP Request

    :param url: Request url
    :type url: str

    :param data_type: Expected response data type
    :type data_type: str

    :param data: Data to send in the request
    :type data: str or dict

    :param data_type: Type of data to send in the request
    :type data_type: str

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

    Log.Debug("Requesting '%s', response_type: '%s'%s" % (
        url,
        response_type,
        ", len(data): %s, data_type: '%s'" % (
            len(data) if data else None,
            data_type
        ) if data else ''
    ))

    return internal_request(
        req,
        response_type,

        **kwargs
    )


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

    # TODO ignore errors?
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
    @classmethod
    def from_exception(cls, e):
        return NetworkError(e.message or str(e), e)


class ParseError(RequestError):
    @classmethod
    def from_exception(cls, e):
        return ParseError(e.message or str(e), e)
