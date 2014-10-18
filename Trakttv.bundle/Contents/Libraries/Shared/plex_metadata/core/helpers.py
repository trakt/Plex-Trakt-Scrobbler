import re


def try_convert(value, value_type, default=None):
    try:
        return value_type(value)
    except ValueError:
        return default
    except TypeError:
        return default


def compile_map(guid_map):
    result = {}

    # Compile agent mapping patterns
    for key, mappings in guid_map.items():
        # Transform into list
        if type(mappings) is not list:
            mappings = [mappings]

        for x, value in enumerate(mappings):
            # Transform into tuple of length 2
            if type(value) is str:
                value = (value, None)
            elif type(value) is tuple and len(value) == 1:
                value = (value, None)

            # Compile pattern
            if value[1]:
                value = (value[0], re.compile(value[1], re.IGNORECASE))

            mappings[x] = value

        result[key] = mappings

    return result
