import arrow


def to_datetime(value):
    if value is None:
        return None

    # Parse ISO8601 datetime
    dt = arrow.get(value)

    # Convert to UTC
    dt = dt.to('UTC')

    # Return naive datetime object
    return dt.naive
