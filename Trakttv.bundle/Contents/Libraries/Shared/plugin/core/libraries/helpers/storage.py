import logging
import os
import shutil

log = logging.getLogger(__name__)


class StorageHelper(object):
    base_names = [
        'plug-ins',
        'plug-in support',
        'trakttv.bundle'
    ]

    @classmethod
    def create_directories(cls, path, *args, **kwargs):
        """Create directory at `path` include any parent directories"""

        try:
            os.makedirs(path, *args, **kwargs)
            return True
        except OSError, ex:
            if ex.errno == 17:
                # Directory already exists
                return True

            log.warn('Unable to create directories: %r - (%s) %s', cls.to_relative_path(path), ex.errno, ex)
        except Exception, ex:
            log.warn('Unable to create directories: %r - (%s) %s', cls.to_relative_path(path), type(ex), ex)

        return False

    @classmethod
    def copy(cls, source, destination):
        """Copy the file at `source` to `destination`"""

        if os.path.isdir(source):
            return cls.copy_tree(source, destination)

        try:
            shutil.copy2(source, destination)

            log.debug('Copied %r to %r', cls.to_relative_path(source), cls.to_relative_path(destination))
            return True
        except Exception, ex:
            log.warn('Unable to copy %r to %r - %s', cls.to_relative_path(source), cls.to_relative_path(destination), ex)

        return False

    @classmethod
    def copy_tree(cls, source, destination):
        """Copy the directory at `source` to `destination`"""

        try:
            shutil.copytree(source, destination)

            log.debug('Copied %r to %r', cls.to_relative_path(source), cls.to_relative_path(destination))
            return True
        except Exception, ex:
            log.warn('Unable to copy %r to %r - %s', cls.to_relative_path(source), cls.to_relative_path(destination), ex)

        return False

    @classmethod
    def delete(cls, path):
        """Delete the file (at `path`)"""

        try:
            os.remove(path)

            log.debug('Deleted %r', cls.to_relative_path(path))
            return True
        except Exception, ex:
            log.warn('Unable to delete file: %r - %s', cls.to_relative_path(path), ex)

        return False

    @classmethod
    def delete_tree(cls, path):
        """Delete the directory (at `path`)"""

        try:
            shutil.rmtree(path)

            log.debug('Deleted %r', cls.to_relative_path(path))
            return True
        except Exception, ex:
            log.warn('Unable to delete directory: %r - %s', cls.to_relative_path(path), ex)

        return False

    @classmethod
    def to_relative_path(cls, path):
        """Convert `path` to be relative to `StorageHelper.base_names`"""

        path_lower = path.lower()

        # Find base path
        base_path = None

        for base in cls.base_names:
            if base not in path_lower:
                continue

            base_path = path[:path_lower.find(base)]
            break

        # Check if `base_path` was found
        if not base_path:
            log.warn('Unable to find base path in %r', path)
            return path

        # Return relative path
        return os.path.relpath(path, base_path)

    @classmethod
    def is_relative_path(cls, path):
        """Check if `path` is relative to `StorageHelper.base_names`"""

        path_lower = path.lower()

        # Ignore framework paths
        if 'framework.bundle' in path_lower:
            return False

        # Find base path
        for base in cls.base_names:
            if base not in path_lower:
                continue

            return True

        return False
