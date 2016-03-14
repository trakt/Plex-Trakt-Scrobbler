from logging import Filter
import logging

log = logging.getLogger(__name__)


class DuplicateReportFilter(Filter):
    def filter(self, record):
        if self.is_duplicate_message(record):
            return False

        return True

    @classmethod
    def is_duplicate_message(cls, record):
        if record.levelno < logging.WARNING:
            return False

        if not record:
            return False

        # Try retrieve "duplicate" attribute from record
        duplicate = getattr(record, 'duplicate', None)

        # Convert to boolean
        return bool(duplicate)
