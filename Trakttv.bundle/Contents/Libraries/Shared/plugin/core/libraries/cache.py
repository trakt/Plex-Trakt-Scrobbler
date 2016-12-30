from plugin.core.environment import Environment
from plugin.core.libraries.constants import CONTENTS_PATH
from plugin.core.libraries.helpers import StorageHelper, SystemHelper

import filecmp
import logging
import os

log = logging.getLogger(__name__)


class CacheManager(object):
    @classmethod
    def sync(cls, cache_path=None):
        """Synchronize native libraries cache, adding/updating/removing items to match bundled libraries.

        :param cache_path: Directory to store cached libraries
        :type cache_path: str

        :rtype: str
        """

        # Set `cache_path` default
        if cache_path is None:
            cache_path = os.path.join(Environment.path.plugin_data, 'Libraries')

        # Retrieve paths for system libraries
        source, destination = cls.get_paths(cache_path)

        if not source or not destination:
            return None

        # Compare directories, discover tasks
        changes = filecmp.dircmp(source, destination)
        tasks = cls.discover(changes)

        # Execute tasks
        if tasks and not cls.execute(source, destination, tasks):
            return None

        return cache_path

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
                # Ignore "*.pyc" files
                if name.endswith('.pyc'):
                    continue

                # Append task to list
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
    def get_paths(cache_path):
        """Retrieve system-specific native libraries source + destination path

        :param cache_path: Directory to store cached libraries
        :type cache_path: str

        :rtype: (str, str)
        """
        # Retrieve system details
        system = SystemHelper.name()
        architecture = SystemHelper.architecture()

        if not architecture:
            return None, None

        # Build list of acceptable architectures
        architectures = [architecture]

        if architecture == 'i686':
            # Fallback to i386
            architectures.append('i386')

        # Look for matching libraries
        for arch in architectures + ['universal']:
            # Build source path
            source = os.path.join(CONTENTS_PATH, 'Libraries', system, arch)

            # Ensure `source` directory exists
            if not os.path.exists(source):
                continue

            # Build path for native dependencies
            destination = os.path.join(cache_path, system, arch)

            # Ensure `destination` directory has been created
            if not StorageHelper.create_directories(destination):
                # Directory couldn't be created
                return None, None

            return source, destination

        # No libraries could be found
        log.info('Unable to cache libraries, couldn\'t find native libraries for platform (name: %r, architecture: %r)', system, architecture)
        return None, None
