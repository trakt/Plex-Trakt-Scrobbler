from plex_metadata import Guid


def log_unsupported_guid(logger, guid):
    if guid is None or guid.agent_id is None:
        return

    if guid and isinstance(guid, Guid):
        logger.warn('Unsupported guid: %%r (agent: %r)' % guid.agent_id, guid.value, extra={
            'original': guid.original,
            'event': {
                'module': __name__,
                'name': 'unsupported_guid',
                'key': (guid.agent_id, guid.value)
            }
        })
    else:
        logger.warn('Unsupported guid: %r', guid, extra={
            'event': {
                'module': __name__,
                'name': 'unsupported_guid',
                'key': guid
            }
        })
