from plugin.sync.modes.core.base.mode import Mode
from plugin.sync.modes.core.base.pull import PullListsMode


def mark_unsupported(dictionary, rating_key, guid, p_item):
    if rating_key in dictionary:
        return

    dictionary[rating_key] = (guid, p_item)


def log_unsupported(logger, message, dictionary):
    if len(dictionary) < 1:
        return

    logger.info(
        message,
        len(dictionary),
        '\n'.join(format_unsupported(dictionary))
    )


def format_unsupported(dictionary):
    keys = sorted(dictionary.keys())

    for key in keys:
        guid, p_item = dictionary[key]

        agent = guid.agent if guid else None
        title = p_item.get('title')
        year = p_item.get('year')

        if title and year:
            yield '    [%6s] GUID agent %r is not supported on: %r (%r)' % (key, agent, title, year)
        else:
            yield '    [%6s] GUID agent %r is not supported' % (key, agent)
