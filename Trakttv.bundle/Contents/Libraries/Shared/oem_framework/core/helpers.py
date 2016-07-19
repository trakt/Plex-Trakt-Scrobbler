from datetime import datetime
import time


def convert_keys_to_string(value):
    if type(value) is not dict:
        return value

    result = {}

    for k, v in value.items():
        if type(k) is not str:
            k = str(k)

        if v is None:
            continue

        if type(v) is dict:
            result[k] = convert_keys_to_string(v)
        elif type(v) is list:
            result[k] = [
                convert_keys_to_string(v)
                for v in v
            ]
        else:
            result[k] = v

    return result


def get_attribute(touched, data, key, default=None):
    try:
        value = data[key]

        touched.add(key)
        return value
    except KeyError:
        return default


def median(lst):
    lst = sorted(lst)

    if len(lst) < 1:
        return None

    if len(lst) % 2 == 1:
        return lst[((len(lst)+1)/2)-1]
    else:
        return float(sum(lst[(len(lst)/2)-1:(len(lst)/2)+1]))/2.0


def timestamp_utc():
    # Retrieve UTC timestamp
    timestamp = time.mktime(datetime.utcnow().timetuple())

    # Round to integer
    return int(round(timestamp, 0))


def try_convert(value, value_type, default=None):
    try:
        return value_type(value)
    except:
        return default
