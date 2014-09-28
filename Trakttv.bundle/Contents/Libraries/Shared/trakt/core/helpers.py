from datetime import datetime


def to_datetime(value):
    if value is None:
        return None

    # Remove time-zone info from datetime string
    value = value[:value.rfind('+')]

    # Parse into datetime object
    return datetime.strptime(value, '%Y-%m-%dT%H:%M:%S.%f')
