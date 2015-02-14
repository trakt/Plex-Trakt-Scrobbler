def merge(a, b):
    a.update(b)
    return a


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
