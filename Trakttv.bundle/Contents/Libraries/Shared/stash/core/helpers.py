def to_integer(value, default=None):
    try:
        return int(value)
    except:
        return default
