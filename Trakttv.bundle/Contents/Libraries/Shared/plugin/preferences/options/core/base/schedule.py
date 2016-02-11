from plugin.models import SchedulerTask, SchedulerJob
from plugin.preferences.options.core.base.base import Option

import logging

log = logging.getLogger(__name__)


class SchedulerOption(Option):
    def __init__(self, preferences, task=None, job=None):
        super(SchedulerOption, self).__init__(preferences, job)

        self._task = task

    @property
    def value(self):
        if self._option is None:
            log.warn('Tried to retrieve value from an option without "get()"')
            return None

        return self._option.trigger

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
            task=self.key,

            defaults={
                'trigger': self.default
            }
        )

        if job.trigger and job.due_at is None:
            job.due_at = self.get_next(job)
            job.save()

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
            task=self.key
        )

        # Update job
        self.update_trigger(job, value)

        # Emit database change to handler (if enabled)
        if emit:
            self._preferences.on_database_changed(self.key, value, account=account)

    def update_trigger(self, job, value):
        if job.trigger == value:
            # Trigger hasn't changed
            return

        # Update `trigger` and `due_at` properties
        job.trigger = value
        job.due_at = self.get_next(job)

        # Save changes
        job.save()

    @classmethod
    def get_next(cls, job):
        if job.trigger is None:
            return None

        return job.next_at()
