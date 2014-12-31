import arrow


def to_datetime(value):
    if value is None:
        return None

    # Parse ISO8601 datetime
    dt = arrow.get(value)

    # Return python datetime object
    return dt.datetime
