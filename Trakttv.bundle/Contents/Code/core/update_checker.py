from core.http import request, RequestError
from core.plugin import PLUGIN_VERSION_BASE, PLUGIN_VERSION_BRANCH
from threading import Timer
import random


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

    def run_once(self, first_run=True, timeout=3, async=False):
        if async:
            Thread.Create(self.run, first_run=first_run, timeout=timeout)
        else:
            self.run(first_run=first_run, timeout=timeout)

    def request(self, first_run=False, timeout=None):
        data = {
            'client_id': self.client_id,
            'version': self.version,
            'platform': Platform.OS.lower()
        }

        parameters = {}
        if timeout is not None:
            parameters['timeout'] = timeout

        try:
            return request(self.server + '/api/ping', data, 'json', **parameters)
        except RequestError, e:
            if first_run and e.code == 408:
                Log.Info(
                    "Unable to check for updates, on startup a "
                    "response needs to be returned in %s seconds (%s)" % (timeout, e.code)
                )
            else:
                Log.Warn("Unable to check for updates, network error (%s)" % e.code)

            Log.Debug('"%s" (%s)' % (e.message, e.code))

        return None

    def reset(self, available=None):
        self.update_available = available
        self.update_detail = None

    def run(self, first_run=False, timeout=None):
        response = self.request(first_run, timeout)
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

        log_func = Log.Info
        if first_run:
            log_func = Log.Debug

        if response.get('update_error'):
            self.reset()

            message = 'Unable to check for updates, ' \
                      'probably on an unsupported branch: "%s"' % response['update_error']

            # Only log the warning on the first result, no need to spam with warnings
            if first_run:
                Log.Warn(message)
            else:
                Log.Debug(message)
        elif response.get('update_available'):
            self.update_available = True
            self.update_detail = response['update_available']

            log_func("Update Available: %s" % self.update_detail['name'])
        else:
            self.reset(False)

            log_func("Up to date")

        self.schedule_next()

    def schedule_next(self, interval=None):
        if interval is None:
            interval = self.interval

        self.timer = Timer(interval, self.run)
        self.timer.start()

        Log.Debug("Next update check scheduled to happen in %s seconds" % interval)
