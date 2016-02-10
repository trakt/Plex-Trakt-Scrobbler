import logging

log = logging.getLogger(__name__)


class CompactTask(object):
    @classmethod
    def run(cls, period, key, revisions, policy):
        log.info('Compacting %s: %r - len(revisions): %r, policy: %r', period, key, len(revisions), policy)

        # Retrieve options
        p_maximum = policy.get('maximum')

        if p_maximum is None:
            raise ValueError('Policy "%s" is missing the "maximum" attribute' % period)

        # Sort revisions by timestamp
        revisions = sorted(revisions, key=lambda b: b.timestamp)

        # Build list of revisions, sorted by time to closest revision
        close_revisions = cls.close_revisions(revisions)

        # Remove closest revisions (by timestamp) until maximum count is reached
        for x in xrange(len(revisions) - p_maximum):
            distance, _, revision = close_revisions[x]

            # Delete revision (metadata + contents)
            revision.delete()

    @staticmethod
    def close_revisions(revisions):
        close_revisions = []

        # Calculate seconds between revisions
        for x in xrange(len(revisions)):
            if x + 1 >= len(revisions):
                continue

            left = revisions[x]
            right = revisions[x + 1]

            # Calculate time between `left` and `right`
            span = right.timestamp - left.timestamp

            # Append item to list
            close_revisions.append((span.total_seconds(), left, right))

        # Sort by closest revisions first
        return sorted(close_revisions, key=lambda item: item[0])
