class PlexAccountExistsException(Exception):
    pass


class TraktAccountExistsException(Exception):
    pass


class FilteredException(Exception):
    pass


class ClientFilteredException(FilteredException):
    pass


class UserFilteredException(FilteredException):
    pass
