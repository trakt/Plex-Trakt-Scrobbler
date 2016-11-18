from plugin.core.backup.models import BackupArchive

import logging
import os
import shutil
import tarfile
import tempfile

log = logging.getLogger(__name__)


class ArchiveTask(object):
    @classmethod
    def run(cls, group, period, key, revisions, policy):
        base_path, date = cls.get_period(group, period, key)

        log.info('Archiving %s: %s (%d revisions, group: %r)', period, date, len(revisions), group)

        # Ensure an archive hasn't already been created
        if os.path.exists(base_path + '.bar') or os.path.exists(base_path + '.tar.gz'):
            log.info('Archive already exists for %r', key)
            return

        # Create archive of revisions
        tar_path, files = cls.create_archive(base_path, revisions)

        # Construct archive metadata
        archive = BackupArchive(
            date=key,
            archive=os.path.basename(tar_path),

            files=[
                os.path.relpath(path, base_path)
                for path in files
            ]
        )

        # Move archive to directory
        try:
            shutil.move(tar_path, base_path + '.tar.gz')
        except Exception as ex:
            log.warn('Unable to move archive to backups directory - %s', ex, exc_info=True)
            return False

        # Write archive metadata
        if not archive.save(base_path + '.bar'):
            # Unable to write metadata
            return False

        # Cleanup archived directory
        cls.cleanup(base_path, files)

        log.info('Archived %s: %s (%d files, group: %r)', period, date, len(files), group)
        return True

    @staticmethod
    def cleanup(base_path, files):
        # Delete files that have been archived
        for path in files:
            try:
                os.remove(path)
            except Exception as ex:
                log.info('Unable to remove file: %r - %s', path, ex, exc_info=True)

        # Delete old directory (if no files exist inside it)
        try:
            os.rmdir(base_path)
        except Exception as ex:
            log.info('Unable to remove directory: %r (probably contains skipped files) - %s', base_path, ex, exc_info=True)

    #
    # Archive creation
    #

    @classmethod
    def create_archive(cls, base_path, revisions):
        # Create temporary path for archive
        path = os.path.join(tempfile.mkdtemp(), os.path.basename(base_path) + '.tar.gz')

        # Create archive
        with tarfile.open(path, 'w:gz') as tar:
            # Add revisions to archive
            files = cls.add_revisions(base_path, tar, revisions)

        return path, files

    @classmethod
    def add_revisions(cls, base_path, tar, revisions):
        files = []

        # Add revisions to tar archive
        for revision in revisions:
            # Add revision metadata
            if not os.path.exists(revision.path):
                continue

            cls.add_file(tar, files, base_path, revision.path)

            # Add revision contents
            directory = os.path.dirname(revision.path)

            for name in revision.contents:
                path = os.path.join(directory, name)

                # Add file from contents
                if not os.path.exists(path):
                    log.warn('Unable to find revision file: %r', path)
                    continue

                cls.add_file(tar, files, base_path, path)

            log.debug('Added revision %r to archive', os.path.basename(revision.path))

        return files

    @staticmethod
    def add_file(tar, tar_files, base_path, path):
        try:
            tar.add(path, arcname=os.path.relpath(path, base_path))
            tar_files.append(path)
        except Exception as ex:
            log.warn('Unable to add file %r to archive - %s', path, ex, exc_info=True)

    #
    # Helpers
    #

    @staticmethod
    def get_period(group, period, key):
        if period == 'month':
            return (
                os.path.join(group.path, str(key[0]), '%02d' % key[1]),
                '%d-%02d' % key
            )

        if period == 'year':
            return (
                os.path.join(group.path, '%d' % key),
                '%d' % key
            )

        raise ValueError('Unsupported archive period: %r' % period)
