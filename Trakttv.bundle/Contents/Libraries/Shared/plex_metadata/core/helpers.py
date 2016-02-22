from plex.lib.six.moves.urllib_parse import urlparse as std_urlparse


def try_convert(value, value_type, default=None):
    try:
        return value_type(value)
    except ValueError:
        return default
    except TypeError:
        return default


def urlparse(url):
    scheme = None
    scheme_pos = url.find('://')

    if scheme_pos != -1:
        scheme = url[:scheme_pos]
        url = url[scheme_pos + 1:]

    return scheme, std_urlparse(url)

