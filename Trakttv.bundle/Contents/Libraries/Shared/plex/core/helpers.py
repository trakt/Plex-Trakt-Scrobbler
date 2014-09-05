def to_iterable(value):
    if value is None:
        return None

    if value and isinstance(value, (list, tuple)):
        return value

    return [value]
