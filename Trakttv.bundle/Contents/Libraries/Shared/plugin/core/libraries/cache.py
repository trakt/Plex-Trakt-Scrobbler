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
        if tasks is None:
            tasks = []

        # Add files to cache
        for name in changes.left_only:
            tasks.append(('add', os.path.join(base_path, name)))

        # Delete files from cache
        for name in changes.right_only:
            tasks.append(('delete', os.path.join(base_path, name)))

        # Update files in cache
        for name in changes.diff_files:
            tasks.append(('update', os.path.join(base_path, name)))

        # Process sub directories
        for name, child in changes.subdirs.items():
            cls.discover(child, os.path.join(base_path, name), tasks)

        # Tasks retrieved
        return tasks

    @classmethod
    def execute(cls, source, destination, tasks):
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
