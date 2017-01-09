from plugin.core.helpers.thread import module
from plugin.core.message import InterfaceMessages
from plugin.managers.core.base import Manager
from plugin.models import ActionHistory, ActionQueue
from plugin.preferences import Preferences

from datetime import datetime, timedelta
from exception_wrappers.libraries import apsw
from exception_wrappers.exceptions import DisabledError
from threading import Thread
from trakt import Trakt
import json
import logging
import peewee
import time

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

        # Retrieve `account_id` for action
        account_id = None

        if session:
            try:
                account_id = session.account_id
            except KeyError:
                account_id = None

        if account_id is None and account:
            account_id = account.id

        if account_id is None:
            log.debug('Unable to find valid account for event %r, session %r', event, session)
            return None

        if not Preferences.get('scrobble.enabled', account_id):
            log.debug('Scrobbler not enabled for account %r', account_id)
            return None

        # Try queue the event
        try:
            obj = ActionQueue.create(
                account=account_id,
                session=session,

                progress=session.progress,

                part=session.part,
                rating_key=session.rating_key,

                event=event,
                request=request,

                queued_at=datetime.utcnow()
            )
            log.debug('Queued %r event for %r', event, session)
        except (apsw.ConstraintError, peewee.IntegrityError) as ex:
            log.info('Event %r has already been queued for session %r: %s', event, session.session_key, ex, exc_info=True)
        except Exception as ex:
            log.warn('Unable to queue event %r for %r: %s', event, session, ex, exc_info=True)

        # Ensure process thread is started
        cls.start()

        return obj

    @classmethod
    def delete(cls, session_id, event):
        ActionQueue.delete().where(
            ActionQueue.session == session_id,
            ActionQueue.event == event
        ).execute()

    #
    # Process
    #
    @classmethod
    def start(cls):
        if cls._process_thread is not None:
            return

        cls._process_thread = Thread(target=cls.run)
        cls._process_thread.daemon = True

        cls._process_thread.start()

    @classmethod
    def run(cls):
        while cls._process_enabled:
            if InterfaceMessages.critical:
                cls._process_enabled = False
                return

            # Retrieve one action from the queue
            try:
                action = ActionQueue.get()
            except ActionQueue.DoesNotExist:
                time.sleep(5)
                continue
            except DisabledError:
                break
            except Exception as ex:
                log.warn('Unable to retrieve action from queue - %s', ex, exc_info=True)
                time.sleep(5)
                continue

            log.debug('Retrieved %r action from queue', action.event)

            try:
                performed = cls.process(action)

                cls.resolve(action, performed)

                log.debug('Action %r sent, moved action to history', action.event)
            except Exception as ex:
                log.warn('Unable to process action %%r - %s' % ex.message, action.event, exc_info=True, extra={
                    'event': {
                        'module': __name__,
                        'name': 'run.process_exception',
                        'key': ex.message
                    }
                })
            finally:
                time.sleep(5)

    @classmethod
    def process(cls, action):
        if not action.request:
            return None

        if cls.is_duplicate(action):
            return None

        interface, method = action.event.split('/')
        request = str(action.request)

        log.debug('Sending action %r (account: %r, interface: %r, method: %r)', action.event, action.account, interface, method)

        try:
            result = cls.send(action, Trakt[interface][method], request)
        except Exception as ex:
            log.error('Unable to send action %r: %r', action.event, ex, exc_info=True)
            return None

        if not result:
            # Invalid response
            return None

        if interface == 'scrobble':
            return result.get('action')

        log.warn('result: %r', result)
        return None

    @classmethod
    def is_duplicate(cls, action):
        if action.event != 'scrobble/stop':
            return False

        # Retrieve scrobble duplication period
        duplication_period = Preferences.get('scrobble.duplication_period')

        if duplication_period is None:
            return False

        # Check for duplicate scrobbles in `duplication_period`
        scrobbled = ActionHistory.has_scrobbled(
            action.account, action.rating_key,
            part=action.part,
            after=action.queued_at - timedelta(minutes=duplication_period)
        )

        if scrobbled:
            log.info(
                'Ignoring duplicate %r action, scrobble already performed in the last %d minutes',
                action.event, duplication_period
            )
            return True

        return False

    @classmethod
    def send(cls, action, func, request):
        # Retrieve `Account` for action
        account = action.account

        if not account:
            log.info('Missing `account` for action, unable to send')
            return None

        # Retrieve request data
        request = json.loads(request)
        log.debug('request: %r', request)

        # Send request with account authorization
        trakt_account = account.trakt

        if trakt_account is None:
            log.info('Missing trakt account for %r', account)
            return None
        
        with trakt_account.authorization():
            return func(**request)

    @classmethod
    def resolve(cls, action, performed):
        # Store action in history
        ActionHistory.create(
            account=action.account_id,
            session=action.session_id,

            part=action.part,
            rating_key=action.rating_key,

            event=action.event,
            performed=performed,

            queued_at=action.queued_at,
            sent_at=datetime.utcnow()
        )

        # Delete queued action
        cls.delete(action.session_id, action.event)
