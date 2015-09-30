from plugin.sync.core.enums import SyncMode
from plugin.sync.modes.core.base import Mode

import logging

log = logging.getLogger(__name__)


class Base(Mode):
    mode = SyncMode.Push

    @classmethod
    def log_pending(cls, message, pending):
        if type(pending) is set:
            items = [
                (k, None)
                for k in pending
            ]
        elif type(pending) is dict:
            items = [
                (k, v)
                for k, v in pending.items()
                if len(v) > 0
            ]
        else:
            raise ValueError('Unknown type for "pending" parameter')

        if len(items) < 1:
            return

        log.info(
            message,
            len(items),
            '\n'.join(cls.format_pending(items))
        )

    @classmethod
    def format_pending(cls, items):
        for key, children in items:
            # Write basic line
            yield '    %s' % (key, )

            if children is None:
                # No list of children (episodes)
                continue

            # Write each child
            for child in children:
                yield '        %s' % (child, )