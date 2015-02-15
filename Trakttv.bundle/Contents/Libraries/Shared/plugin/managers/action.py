from plugin.core.helpers.thread import module
from plugin.managers.core.base import Manager
from plugin.models import db, ActionHistory, ActionQueue

from datetime import datetime
from threading import Thread
from trakt import Trakt
import apsw
import json
import logging
import time
import traceback

log = logging.getLogger(__name__)


@module(start=True, blocking=True)
class ActionManager(Manager):
    _process_enabled = True
    _process_thread = None

    #
    # Queue
    #

    @classmethod
    def queue(cls, event, request, session=None, account=None):
        if event is None:
            return None

        obj = None

        if request is not None:
            request = json.dumps(request)

        # Try queue the event
        try:
            obj = ActionQueue.create(
                account=session.account_id if session else account,
                session=session,

                event=event,
                request=request,

                queued_at=datetime.utcnow()
            )
            log.debug('Queued %r event for %r', event, session)
        except apsw.ConstraintError:
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
                time.sleep(5)
                continue

            interface, method = action.event.split('/')

            log.debug('Sending action %r (interface: %r, method: %r)', action.event, interface, method)

            result = None

            if action.request:
                request = str(action.request)

                try:
                    request = json.loads(request)

                    log.debug('request: %r', request)

                    result = Trakt[interface][method](**request)
                except Exception, ex:
                    log.error('Unable to send action %r: %r', action.event, ex, exc_info=True)

            if interface == 'scrobble':
                performed = result.get('action')
            else:
                log.warn('result: %r', result)
                performed = None

            # Store action in history
            ActionHistory.create(
                account=action.account_id,
                session=action.session_id,

                event=action.event,
                performed=performed,

                queued_at=action.queued_at,
                sent_at=datetime.utcnow()
            )

            # Delete queued action
            ActionQueue.delete().where(
                ActionQueue.session == action.session_id,
                ActionQueue.event == action.event
            ).execute()

            log.debug('Action %r sent, moved action to history', action.event)
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
        if last == 'scrobble/start':
            # Already sent a "start" action
            return None

        if 'scrobble/start' in queue:
            # "start" action already queued
            return None

        return 'scrobble/start'

    @classmethod
    def decide_paused(cls, session, history, last, queue):
        if last == 'scrobble/pause':
            # Already sent a "pause" action
            return None

        if last != 'scrobble/start':
            # Haven't sent a "start" action yet, nothing to pause
            return None

        if 'scrobble/pause' in queue:
            # "pause" action already queued
            return None

        return 'scrobble/pause'

    @classmethod
    def decide_stopped(cls, session, history, last, queue):
        if last == 'scrobble/stop':
            # Already sent a "stop" action
            return None

        if last not in ['scrobble/start', 'scrobble/pause']:
            # Previous action wasn't a "start" or "pause" event
            return None

        if 'scrobble/stop' in queue:
            # "stop" action already queued
            return None

        return 'scrobble/stop'

    #
    # Misc
    #

    @classmethod
    def get_events(cls, items):
        return [
            item.event
            for item in items
        ]
