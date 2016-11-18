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
            return cls.build_failure('No tests defined')

        # Run tests
        for name in names:
            # Ensure function exists
            if not hasattr(cls, name):
                return cls.build_failure('Unable to find function: %r' % name)

            # Run test
            try:
                result = cls.spawn(name, search_paths)

                # Merge test result into `metadata`
                merge(metadata, result, recursive=True)

                # Test successful
                message = None
                success = True
            except Exception as ex:
                if success:
                    continue

                message = ex.message
                success = False

        if not success:
            # Trigger event
            cls.on_failure(message)

            # Build result
            return cls.build_failure(message)

        # Trigger event
        cls.on_success(metadata)

        # Build result
        return cls.build_success(metadata)

    @classmethod
    def spawn(cls, name, search_paths):
        # Find path to python executable
        python_exe = cls.find_python_executable()

        if not python_exe:
            raise Exception('Unable to find python executable')

        # Ensure test host exists
        if not os.path.exists(HOST_PATH):
            raise Exception('Unable to find "host.py" script')

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

        # Parse output
        result = None

        if stdout:
            try:
                result = json.loads(stdout)
            except Exception as ex:
                log.warn('Invalid output returned %r - %s', stdout, ex, exc_info=True)

        # Build result
        if process.returncode != 0:
            # Test failed
            if result and result.get('message'):
                if result.get('traceback'):
                    log.info('%s - %s', result['message'], result['traceback'])

                raise Exception(result['message'])

            raise Exception('Unknown error (code: %s)' % process.returncode)

        # Test successful
        return result

    @classmethod
    def find_python_executable(cls):
        candidates = [sys.executable]

        # Add candidates based on the script path in `sys.argv`
        if sys.argv and len(sys.argv) > 0 and os.path.exists(sys.argv[0]):
            bootstrap_path = sys.argv[0]
            resources_pos = bootstrap_path.lower().find('resources')

            if resources_pos > 0:
                pms_path = bootstrap_path[:resources_pos]

                cls._add_python_home_candidates(candidates, pms_path)

        # Add candidates relative to `PLEX_MEDIA_SERVER_HOME`
        pms_home = os.environ.get('PLEX_MEDIA_SERVER_HOME')

        if pms_home and os.path.exists(pms_home):
            cls._add_python_home_candidates(candidates, pms_home)

        # Add candidates relative to `PYTHONHOME`
        python_home = os.environ.get('PYTHONHOME')

        if python_home and os.path.exists(python_home):
            candidates.append(os.path.join(python_home, 'bin', 'python'))

        # Use first candidate that exists
        for path in candidates:
            if os.path.exists(path):
                return path

        log.warn('Unable to find python executable', extra={'candidates': candidates})
        return None

    @staticmethod
    def _add_python_home_candidates(candidates, path):
        # Windows
        candidates.append(os.path.join(path, 'PlexScriptHost.exe'))

        # *nix
        candidates.append(os.path.join(path, 'Plex Script Host'))
        candidates.append(os.path.join(path, 'Resources', 'Plex Script Host'))
        candidates.append(os.path.join(path, 'Resources', 'Python', 'bin', 'python'))

    #
    # Events
    #

    @classmethod
    def on_failure(cls, message):
        pass

    @classmethod
    def on_success(cls, metadata):
        pass

    #
    # Helpers
    #

    @classmethod
    def build_exception(cls, message, exc_info=None):
        if exc_info is None:
            exc_info = sys.exc_info()

        return cls.build_failure(
            message,
            exc_info=exc_info
        )

    @classmethod
    def build_failure(cls, message, **kwargs):
        result = {
            'success': False,
            'message': message
        }

        # Merge extra attributes
        merge(result, kwargs)

        return result

    @staticmethod
    def build_success(metadata):
        return {
            'success': True,
            'metadata': metadata
        }
