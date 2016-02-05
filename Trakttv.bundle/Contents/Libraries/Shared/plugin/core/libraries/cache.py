from plugin.core.environment import Environment
from plugin.core.libraries.constants import CONTENTS_PATH
from plugin.core.libraries.helpers import StorageHelper, SystemHelper

import filecmp
import logging
import os

log = logging.getLogger(__name__)


class CacheManager(object):
    @classmethod
    def sync(cls):
        """Synchronize native libraries cache, adding/updating/removing items to match bundled libraries.

        :rtype: str
        """

        source, destination = cls.get_paths()

        # Compare directories, discover tasks
        changes = filecmp.dircmp(source, destination)
        tasks = cls.discover(changes)

        # Execute tasks
        if tasks and not cls.execute(source, destination, tasks):
            return None

        return os.path.join(Environment.path.plugin_data, 'Libraries')

    @classmethod
    def discover(cls, changes, base_path='', tasks=None):
        """"Discover actions required to update the cache.

        :param changes: Changes between bundle + cache directories
        :type changes: filecmp.dircmp

        :param base_path: Current directory of changes
        :type base_path: str

        :param tasks: Current tasks
        :type tasks: list or None

        :rtype: list
        """
        if tasks is None:
            tasks = []

        def process(action, names):
            for name in names:
                tasks.append((action, os.path.join(base_path, name)))

        # Create tasks from `changes`
        process('add', changes.left_only)
        process('delete', changes.right_only)
        process('update', changes.diff_files)

        # Process sub directories
        for name, child in changes.subdirs.items():
            cls.discover(child, os.path.join(base_path, name), tasks)

        # Tasks retrieved
        return tasks

    @classmethod
    def execute(cls, source, destination, tasks):
        """Execute tasks on directories

        :param source: Native libraries source directory
        :type source: str

        :param destination: Native libraries cache directory
        :type destination: str

        :param tasks: Tasks to execute
        :type tasks: list

        :rtype: bool
        """
        success = True

        for action, path in tasks:
            if action in ['add', 'update']:
                action_success = StorageHelper.copy(os.path.join(source, path), os.path.join(destination, path))
            elif action == 'delete':
                action_success = StorageHelper.delete(os.path.join(destination, path))
            else:
                log.warn('Unknown task: %r - %r', action, path)
                action_success = False

            if not action_success:
                success = False

        return success

    @staticmethod
    def get_paths():
        """Retrieve system-specific native libraries source + destination path

        :rtype: (str, str)
        """
        # Retrieve system details
        system = SystemHelper.name()
        architecture = SystemHelper.architecture()

        if not architecture:
            return

        # Build source path
        source = os.path.join(CONTENTS_PATH, 'Libraries', system, architecture)

        # Ensure `source` directory exists
        if not os.path.exists(source):
            log.error('Unable to find native libraries for platform (name: %r, architecture: %r)', system, architecture)
            return None

        # Build path for native dependencies
        destination = os.path.join(Environment.path.plugin_data, 'Libraries', system, architecture)

        # Ensure `destination` directory has been created
        StorageHelper.create_directories(destination)

        return source, destination
