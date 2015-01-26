from core.logger import Logger
from plugin.core.constants import PLUGIN_VERSION_BASE, PLUGIN_VERSION_BRANCH

from threading import Timer
import json
import random
import requests

log = Logger('core.update_checker')


class UpdateChecker(object):
    # interval = 24 hours + random offset between 0 - 60 minutes
    interval = (24 * 60 * 60) + (random.randint(0, 60) * 60)

    server = 'http://pts.skipthe.net'

    def __init__(self):
        self.timer = None

        self.version = {
            'base': '.'.join([str(x) for x in PLUGIN_VERSION_BASE]),
            'branch': PLUGIN_VERSION_BRANCH
        }

        self.client_id = None

        self.update_available = None
        self.update_detail = None

        # Retrieve the saved client_id if one exists
        if 'client_id' in Dict:
            self.client_id = Dict['client_id']

    def start(self):
        self.run_once(async=True)

    def run_once(self, first_run=True, async=False):
        if async:
            Thread.Create(self.run, first_run=first_run)
        else:
            self.run(first_run=first_run)

    def request(self, first_run=False):
        data = {
            'client_id': self.client_id,
            'version': self.version,
            'platform': Platform.OS.lower()
        }

        response = requests.post(self.server + '/api/ping', data=json.dumps(data))
        if not response:
            return None

        return response.json()

    def reset(self, available=None):
        self.update_available = available
        self.update_detail = None

    def run(self, first_run=False):
        if Dict['developer']:
            log.info('Developer mode enabled, update checker disabled')
            return

        response = self.request(first_run)
        if response is None:
            # Schedule a re-check in 30 seconds on errors
            self.reset()
            self.schedule_next(30)
            return

        # Store our new client_id for later use
        if not self.client_id and 'client_id' in response:
            self.client_id = response['client_id']

            Dict['client_id'] = self.client_id
            Dict.Save()

        self.process_response(first_run, response)

        self.schedule_next()

    def process_response(self, first_run, response):
        log_func = log.debug if first_run else log.info

        if response.get('update_error'):
            self.reset()

            message = 'Unable to check for updates, ' \
                      'probably on an unsupported branch: "%s"' % response['update_error']

            # Only log the warning on the first result, no need to spam with warnings
            if first_run:
                log.info(message)
            else:
                log.debug(message)
        elif response.get('update_available'):
            self.update_available = True
            self.update_detail = response['update_available']

            log_func("Update Available: %s" % self.update_detail['name'])
        else:
            self.reset(False)

            log_func("Up to date")

    def schedule_next(self, interval=None):
        if interval is None:
            interval = self.interval

        self.timer = Timer(interval, self.run)
        self.timer.start()

        log.debug("Next update check scheduled to happen in %s seconds" % interval)
