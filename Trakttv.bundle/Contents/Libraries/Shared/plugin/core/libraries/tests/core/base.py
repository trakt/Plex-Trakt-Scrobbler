from plugin.core.helpers.variable import merge

from subprocess import Popen
import json
import logging
import os
import subprocess
import sys

CURRENT_PATH = os.path.abspath(__file__)
HOST_PATH = os.path.join(os.path.dirname(CURRENT_PATH), 'host.py')

log = logging.getLogger(__name__)


class BaseTest(object):
    name = None
    optional = False

    @classmethod
    def run(cls, search_paths):
        metadata = {}

        message = None
        success = None

        # Retrieve names of test functions
        names = [
            name for name in dir(cls)
            if name.startswith('test_')
        ]

        if not names:
            return cls.on_failure('No tests defined')

        # Run tests
        for name in names:
            # Ensure function exists
            if not hasattr(cls, name):
                return cls.on_failure('Unable to find function: %r' % name)

            # Run test
            try:
                result = cls.spawn(name, search_paths)

                if not result:
                    continue

                # Update `success` status
                if not success:
                    message = result.get('message')
                    success = result.get('success', False)

                # Merge function result into `metadata`
                merge(metadata, result.get('metadata', {}), recursive=True)
            except Exception, ex:
                return cls.on_exception('Exception raised in %r: %s' % (name, ex))

        if not success:
            return cls.on_failure(message)

        return cls.on_success(metadata)

    @classmethod
    def spawn(cls, name, search_paths):
        # Retrieve path to python executable
        python_exe = sys.executable

        if not os.path.exists(python_exe):
            return cls.on_failure('Unable to find python executable')

        if not os.path.exists(HOST_PATH):
            return cls.on_failure('Unable to find "host.py" script')

        # Build test process arguments
        args = [
            python_exe, HOST_PATH,
            '--module', cls.__module__,
            '--name', name,

            '--search-paths="%s"' % (
                ';'.join(search_paths)
            ),
        ]

        # Spawn test (in sub-process)
        log.debug('Starting test: %s:%s', cls.__module__, name)

        process = Popen(
            args,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )

        # Wait for test to complete
        stdout, stderr = process.communicate()

        if stderr:
            log.debug('Test returned messages:\n%s', stderr.replace("\r\n", "\n"))

        # Parse result
        result = None

        if stdout:
            try:
                result = json.loads(stdout)
            except Exception, ex:
                log.warn('Invalid output returned %r - %s', stdout, ex, exc_info=True)

        if process.returncode == 0:
            return cls.on_success(result)
        elif result and 'message' in result:
            return cls.on_exception(result['message'])

        # Display test error details
        return cls.on_failure('Unknown error (code: %s)' % process.returncode)

    #
    # Events
    #

    @classmethod
    def on_exception(cls, message, exc_info=None):
        if exc_info is None:
            exc_info = sys.exc_info()

        return cls.on_failure(
            message,
            exc_info=exc_info
        )

    @classmethod
    def on_failure(cls, message, **kwargs):
        result = {
            'success': False,
            'message': message
        }

        # Merge extra attributes
        merge(result, kwargs)

        return result

    @staticmethod
    def on_success(metadata):
        return {
            'success': True,
            'metadata': metadata
        }
