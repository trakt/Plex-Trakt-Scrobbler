from plugin.core.constants import PLUGIN_VERSION_BASE, PLUGIN_VERSION_BRANCH
from plugin.core.environment import Environment
from plugin.managers.message import MessageManager
from plugin.models import Message
from plugin.modules.core.base import Module

import json
import logging
import os

VERSION_PATH = os.path.abspath(os.path.join(Environment.path.code, '..', '.version'))

log = logging.getLogger(__name__)


class Upgrade(Module):
    __key__ = 'upgrade'

    def __init__(self):
        pass

    def start(self):
        log.debug('Checking for version change...')

        current = self.current()
        installed = self.installed()

        # New install
        if current is None:
            self.update(installed)
            return

        # Validate
        changed, valid = self.validate(current, installed)

        if not changed or not valid:
            return

        # Update current version
        self.update(installed)

    @classmethod
    def validate(cls, current, installed):
        # No change
        if current == installed:
            log.debug('No change')
            return False, True

        # Downgrade
        if tuple(installed['version']) < tuple(current['version']):
            cls.log(
                logging.WARN, Message.Code.DowngradeUnclean,
                message='Detected un-clean downgrade',
                description="Try delete the \"Trakttv.bundle\" directory first, then install the older version "
                            "of the plugin"
            )
            return True, False

        # Upgrade
        if tuple(installed['version']) > tuple(current['version']):
            cls.log(
                logging.INFO, Message.Code.UpgradePerformed,
                message='Plugin has been updated to v%s' % cls.format(installed)
            )
            return True, True

        # Invalid
        return False, False

    @classmethod
    def log(cls, level, code, message, description=None):
        # Write to log file
        log.log(level, message)

        # Store message in database
        MessageManager.get.from_message(
            level, message,

            code=code,
            description=(description or message)
        )

    @classmethod
    def current(cls):
        if not os.path.exists(VERSION_PATH):
            return None

        try:
            with open(VERSION_PATH, 'rb') as fp:
                data = json.load(fp)

            if 'version' not in data:
                return None

            if 'branch' not in data:
                return None

            return data
        except Exception as ex:
            log.warn('Unable to read current version: %s', ex, exc_info=True)

        return None

    @classmethod
    def installed(cls):
        return {
            'version': list(PLUGIN_VERSION_BASE),
            'branch': PLUGIN_VERSION_BRANCH
        }

    @classmethod
    def update(cls, data):
        try:
            with open(VERSION_PATH, 'wb') as fp:
                json.dump(data, fp)

            log.debug('Version updated to %r', data)
            return True
        except Exception as ex:
            log.warn('Unable to write current version: %s', ex, exc_info=True)

        return False

    @staticmethod
    def format(data):
        if 'version' not in data:
            return None

        if 'branch' not in data:
            return None

        return '%s-%s' % (
            '.'.join([
                str(x) for x in data['version']
            ]),
            data['branch']
        )
