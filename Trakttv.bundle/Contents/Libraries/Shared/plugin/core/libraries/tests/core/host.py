from argparse import ArgumentParser
import importlib
import inspect
import json
import logging
import os
import sys
import traceback

log = logging.getLogger(__name__)

PLUGIN_IDENTIFIER = 'trakttv.bundle'


def get_bundle_path():
    bundle_path = os.path.dirname(os.path.abspath(__file__))

    # Find plugin identifier
    pos = bundle_path.lower().find(PLUGIN_IDENTIFIER)

    if pos < 0:
        return None

    # Return bundle path
    return bundle_path[:pos + len(PLUGIN_IDENTIFIER)]


def setup(search_paths):
    # Find bundle path
    bundle_path = get_bundle_path()

    if not bundle_path:
        raise Exception("Unable to find bundle path")

    log.debug("bundle_path: %r", bundle_path)

    # Setup library search paths
    for path in (search_paths or []):
        if not os.path.exists(path):
            continue

        sys.path.insert(0, path)

    # Set environment variable (to disable plugin fixes)
    os.environ['TFP_TEST_HOST'] = 'true'
    return True


def import_module(name):
    log.info("Importing module %r", name)

    module = importlib.import_module(name)

    if not module:
        raise Exception('Unable to import module %r' % name)

    log.info('Imported module: %r', module)
    return module


def find_test(module):
    for key in dir(module):
        value = getattr(module, key, None)

        if not value:
            continue

        if not inspect.isclass(value):
            continue

        if value.__module__ != module.__name__:
            continue

        return value

    return None


def run():
    # Parse arguments
    parser = ArgumentParser()
    parser.add_argument('--debug', action='store_true')
    parser.add_argument('--module', required=True)
    parser.add_argument('--name', required=True)
    parser.add_argument('--search-paths', required=True)

    args = parser.parse_args()

    search_paths = args.search_paths.strip('"').split(';')

    log.debug('module: %r', args.module)
    log.debug('name: %r', args.name)
    log.debug('search_paths: %r', search_paths)

    # Setup logging
    logging.basicConfig(level=logging.DEBUG if args.debug else logging.WARN)

    # Setup test host
    if not setup(search_paths):
        raise Exception("Unable to setup test host")

    # Import test module
    module = import_module(args.module)

    if not module:
        raise Exception("Unable to import test module: %r" % args.module)

    # Find test class
    cls = find_test(module)

    if not cls:
        raise Exception('Unable to find test class in %r' % args.module)

    # Find test method
    func = getattr(cls, args.name)

    if not func:
        raise Exception('Unable to find test method %r in %r' % (args.name, cls))

    # Run test
    return func()


if __name__ == '__main__':
    success = True

    try:
        result = run()
    except Exception as ex:
        tb = traceback.format_exc()

        result = {
            'message': ex.message,
            'traceback': tb
        }
        success = False

    sys.stdout.write(json.dumps(result))
    sys.stdout.flush()

    if not success:
        exit(1)
