from logging import Filter
import logging

log = logging.getLogger(__name__)

REPORTED_EVENTS = {}


class EventsReportFilter(Filter):
    def filter(self, record):
        if self.is_event(record):
            return self.process_event(record)

        return True

    @classmethod
    def is_event(cls, record):
        if record.levelno < logging.WARNING:
            return False

        if not record:
            return False

        return hasattr(record, 'event')

    @classmethod
    def process_event(cls, record):
        # Retrieve event details
        event = getattr(record, 'event')

        if not event or type(event) is not dict:
            log.debug('Invalid event details: %r', event)
            return True

        # Remove "event" attribute from record (so it isn't included in error reports)
        try:
            delattr(record, 'event')
        except Exception as ex:
            log.debug('Unable to remove "event" attribute from record - %s', ex, exc_info=True)

        # Check if event has already been reported
        key = (
            event.get('module'),
            event.get('name'),
            event.get('key')
        )

        if key in REPORTED_EVENTS:
            return False

        # Mark event as reported
        REPORTED_EVENTS[key] = True
        return True
