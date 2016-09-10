from plugin.sync.modes.core.base.mode import Mode
from plugin.sync.modes.core.base.pull import PullListsMode

IGNORED_AGENTS = [
    'com.plexapp.agents.none',
    'local',
    'plex'
]


def mark_unsupported(dictionary, rating_key, guid):
    agent = guid.agent_id if guid else None

    if agent not in dictionary:
        dictionary[agent] = {
            'values': set(),
            'rating_keys': set()
        }

    if guid.value:
        dictionary[agent]['values'].add(guid.value)

    dictionary[agent]['rating_keys'].add(rating_key)


def log_unsupported(logger, message, dictionary):
    if len(dictionary) < 1:
        return

    items_count = 0

    # Display individual warnings for each agent
    for agent, details in dictionary.items():
        items_count += len(details['values'])

        if agent is None or agent in IGNORED_AGENTS:
            logger.info('Unsupported agent: %s (%%d items)' % agent, len(details['rating_keys']))
            continue

        # Log unsupported agent warning
        logger.warn('Unsupported agent: %s (%%d items)' % agent, len(details['rating_keys']), extra={
            'values': list(details['values'])[:10],
            'event': {
                'module': __name__,
                'name': 'unsupported_agent',
                'key': agent
            }
        })

    # Display unsupported agent list
    logger.info(message, items_count)
