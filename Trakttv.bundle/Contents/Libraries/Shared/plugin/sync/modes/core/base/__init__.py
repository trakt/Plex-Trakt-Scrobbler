from plugin.sync.modes.core.base.mode import Mode
from plugin.sync.modes.core.base.pull import PullListsMode

unsupported_services = {
    'none': True,
    'plex': True
}


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
        if service not in unsupported_services:
            # First occurrence of unsupported service
            logger.warn('Unsupported service: %s' % service)

            # Mark unsupported service as "seen"
            unsupported_services[service] = True
            continue

        # Duplicate occurrence of unsupported service
        logger.warn('Unsupported service: %s' % service, extra={
            'duplicate': True
        })
