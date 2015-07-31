from plugin.models import SchedulerTask, SchedulerJob
from plugin.preferences.options.core.base.base import Option


class SchedulerOption(Option):
    def __init__(self, preferences, task=None, job=None):
        super(SchedulerOption, self).__init__(preferences, job)

        self._task = task

    def get(self, account=None):
        # Verify get() call is valid
        if self.scope == 'account':
            if account is None:
                raise ValueError('Account option requires the "account" parameter')

            if not self._validate_account(account):
                raise ValueError('Invalid value for "account" parameter: %r' % account)

        if self.scope == 'server' and account is not None:
            raise ValueError("Server option can't be called with the \"account\" parameter")

        # Get/Create `SchedulerTask`
        task, _ = SchedulerTask.get_or_create(
            key=self.key
        )

        # Get/Create `SchedulerJob`
        job, _ = SchedulerJob.get_or_create(
            account=account or 0,
            task=task
        )

        return self._clone(task, job)

    def update(self, value, account=None, emit=True):
        if self.scope == 'account':
            if account is None:
                raise ValueError('Account option requires the "account" parameter')

            if not self._validate_account(account):
                raise ValueError('Invalid value for "account" parameter: %r' % account)

        if self.scope == 'server' and account is not None:
            raise ValueError("Server option can't be called with the \"account\" parameter")

        # Get/Create `SchedulerTask`
        task, _ = SchedulerTask.get_or_create(
            key=self.key
        )

        # Get/Create `SchedulerJob`
        job, _ = SchedulerJob.get_or_create(
            account=account or 0,
            task=task
        )

        # Update job
        if job.trigger != value:
            # Update `trigger` and `due_at` properties
            job.trigger = value

            if value is not None:
                job.due_at = job.next_at
            else:
                job.due_at = None

            # Save changes
            job.save()

        # Emit database change to handler (if enabled)
        if emit:
            self._preferences.on_database_changed(self.key, value, account=account)
