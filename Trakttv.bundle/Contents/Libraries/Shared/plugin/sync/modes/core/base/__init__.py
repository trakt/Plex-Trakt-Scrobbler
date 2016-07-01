from plugin.sync.modes.core.base.mode import Mode
from plugin.sync.modes.core.base.pull import PullListsMode

IGNORED_SERVICES = [
    'none',
    'plex'
]


def mark_unsupported(dictionary, rating_key, guid):
    service = guid.service if guid else None

    if service not in dictionary:
        dictionary[service] = []

    dictionary[service].append(rating_key)


def log_unsupported(logger, message, dictionary):
    if len(dictionary) < 1:
        return

    # Display unsupported service list
    logger.info(message, len(dictionary))

    # Display individual warnings for each service
    for service in dictionary.keys():
        if service is None or service in IGNORED_SERVICES:
            logger.info('Ignoring service: %s' % service)
            continue

        # Log unsupported service warning
        logger.warn('Unsupported service: %s' % service, extra={
            'event': {
                'module': __name__,
                'name': 'unsupported_service',
                'key': service
            }
        })
