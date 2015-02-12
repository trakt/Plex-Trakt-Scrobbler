from plugin.core.helpers.variable import merge
from plugin.managers.core.base import Manager
from plugin.models import db, ActionHistory, ActionQueue

from datetime import datetime
from threading import Thread
import logging
import peewee
import time

log = logging.getLogger(__name__)


class ActionManager(Manager):
    _process_enabled = True
    _process_thread = None

    #
    # Queue
    #

    @classmethod
    def queue(cls, session, event):
        if event is None:
            return None

        obj = None

        # Try queue the event
        try:
            obj = ActionQueue.create(
                account=session.account_id,
                session=session,

                event=event,
                queued_at=datetime.utcnow()
            )
            log.debug('Queued %r event for %r', event, session)
        except peewee.IntegrityError:
            log.warn('Unable to queue event %r for %r', event, session)

        # Ensure process thread is started
        cls.start()

        return obj

    #
    # Process
    #
    @classmethod
    def start(cls):
        if cls._process_thread is not None:
            return

        cls._process_thread = Thread(target=cls.process)
        cls._process_thread.start()

    @classmethod
    def process(cls):
        while cls._process_enabled:
            # Retrieve one action from the queue
            try:
                action = ActionQueue.get()
            except Exception, ex:
                log.debug('Waiting 15 seconds before checking the queue again...')
                time.sleep(15)
                continue

            log.debug('Sending action %r', action.event)

            # TODO actually send the trakt.tv action

            # Store action in history
            ActionHistory.create(
                account=action.account_id,
                session=action.session_id,

                event=action.event,
                performed=action.event,  # TODO this should be from the response returned

                queued_at=action.queued_at,
                sent_at=datetime.utcnow()
            )

            # Delete queued action
            ActionQueue.delete().where(
                ActionQueue.session == action.session_id,
                ActionQueue.event == action.event
            ).execute()

            log.debug('Action %r sent, moved action to history', action.event)

            log.debug('Waiting 5 seconds before sending the next action...')
            time.sleep(5)

    #
    # Decide
    #

    @classmethod
    def decide(cls, session):
        # Retrieve history/queue for session
        history = cls.get_events(session.action_history)
        last = history[-1] if history else None

        queue = cls.get_events(session.action_queue)

        log.debug('session: %r, history: %r, queue: %r', session, list(history), list(queue))

        # Handle session state
        func = getattr(cls, 'decide_%s' % session.state, None)

        if not func:
            # State handler not implemented
            log.warn('Handler for %r is not available', session.state)
            return None

        # Run state handlers
        return func(session, history, last, queue)

    @classmethod
    def decide_playing(cls, session, history, last, queue):
        if last == 'start':
            # Already sent a "start" action
            return None

        if 'start' in queue:
            # "start" action already queued
            return None

        return 'start'

    @classmethod
    def decide_paused(cls, session, history, last, queue):
        if last == 'pause':
            # Already sent a "pause" action
            return None

        if last != 'start':
            # Haven't sent a "start" action yet, nothing to pause
            return None

        if 'pause' in queue:
            # "pause" action already queued
            return None

        return 'pause'

    @classmethod
    def decide_stopped(cls, session, history, last, queue):
        if last == 'stop':
            # Already sent a "stop" action
            return None

        if last not in ['start', 'pause']:
            # Previous action wasn't a "start" or "pause" event
            return None

        if 'stop' in queue:
            # "stop" action already queued
            return None

        return 'stop'

    #
    # Misc
    #

    @classmethod
    def get_events(cls, items):
        return [
            item.event
            for item in items
        ]
