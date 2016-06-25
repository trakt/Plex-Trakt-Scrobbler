from oem_framework.core.elapsed import Elapsed
from oem_framework.plugin import Plugin

import imp
import inspect
import logging
import os
import six
import sys

log = logging.getLogger(__name__)

PLUGIN_KEYS = [
    'database',
    'format',
    'storage'
]

MODULE_PREFIXES = [
    'oem_database_',
    'oem_format_',
    'oem_storage_'
]

PACKAGE_PREFIXES = [
    'oem-database-',
    'oem-format-',
    'oem-storage-'
]


def construct_collection(value):
    result = {}

    for key in PLUGIN_KEYS:
        if value == 'dict':
            result[key] = {}
        elif value == 'list':
            result[key] = []
        else:
            raise ValueError('Unknown value provided for "value" parameter')

    return result


class PluginManager(object):
    search_paths = [os.path.abspath(os.curdir)]

    _available = construct_collection('dict')
    _loaded    = construct_collection('dict')
    _ordered   = construct_collection('list')

    @classmethod
    def discover(cls):
        # Reset current state
        cls._available = construct_collection('dict')
        cls._loaded    = construct_collection('dict')
        cls._ordered   = construct_collection('list')

        # Discover available plugins
        for package_name, descriptor in cls._list_plugins():
            # Parse plugin name
            kind, key = cls._parse_package_name(package_name)

            # Find child plugins
            children = []

            for filename in os.listdir(descriptor['package_path']):
                if not filename.endswith('.py'):
                    continue

                if filename.startswith('__init__.') or filename.startswith('main.'):
                    continue

                name, _ = os.path.splitext(filename)

                children.append('%s/%s' % (key, name))

            for k in [key] + children:
                # Store available plugin
                if k in cls._available[kind]:
                    if cls._available[kind][k]['package_path'] == descriptor['package_path']:
                        # Plugin has already been found
                        continue

                    log.warn('Found multiple installations of %r, using installation at %r', package_name, cls._available[kind][k])
                    continue

                cls._available[kind][k] = descriptor

                log.debug('Found %s: %s', kind, k)

    @classmethod
    def get(cls, kind, key):
        # Ensure plugin is loaded
        if not cls.load(kind, key):
            return None

        # Return loaded plugin
        return cls._loaded[kind][key]

    @classmethod
    def has(cls, kind, key):
        return key in cls._available[kind]

    @classmethod
    def list(cls, kind):
        for key, descriptor in cls._available[kind].items():
            # Ensure plugin is loaded
            if not cls.load(kind, key):
                continue

            # Yield plugin
            yield key, cls._loaded[kind][key]

    @classmethod
    def list_ordered(cls, kind):
        # Ensure available plugins are loaded
        for key, descriptor in cls._available[kind].items():
            if not cls.load(kind, key):
                continue

        # Return plugins in order
        return cls._ordered[kind]

    @classmethod
    @Elapsed.track
    def load(cls, kind, key):
        if key in cls._loaded[kind]:
            # Plugin already loaded
            return True

        # Parse module `key`
        plugins = cls._parse_plugins_key(key)

        for name, module_name in plugins:
            # Retrieve plugin installation descriptor
            descriptor = cls._available[kind].get(name)

            if descriptor is None:
                # Missing plugin
                log.warn('Unable to find installation of %r plugin', name)
                return False
            elif descriptor is False:
                # Ignored plugin
                return False

            # Try load the plugin module
            module = cls._load_module(descriptor, module_name)

            if module is None:
                # Mark plugin as ignored
                cls._available[kind][name] = False
                return False

        # Find plugin class
        plugin = None

        for value in six.itervalues(module.__dict__):
            if not inspect.isclass(value):
                continue

            if value.__module__ != module.__name__:
                continue

            if not issubclass(value, Plugin):
                continue

            if value.__key__ is None:
                continue

            # Found plugin
            plugin = value
            break

        if plugin is None:
            return False

        # Store plugin in dictionary
        cls._loaded[kind][key] = plugin

        # Store plugin in priority list
        cls._insert_plugin(cls._ordered[kind], (key, plugin), key=lambda x: x[1].__priority__)

        log.info('Loaded %s: %r', kind, key)
        return True

    @classmethod
    def _parse_plugins_key(cls, key):
        if not key:
            return None, None

        plugins = key.split('+')

        result = []

        # Parse plugin dependencies
        for plugin_key in plugins:
            # Parse plugin key
            plugin_name, plugin_module = cls._parse_plugin_key(plugin_key)

            if not plugin_name or not plugin_module:
                continue

            result.append((plugin_name, plugin_module))

        # Add main plugin
        result.append(cls._parse_plugin_key(key.replace('+', '-')))

        return result

    @classmethod
    def _parse_plugin_key(cls, key):
        # Parse plugin name
        fragments = key.split('/', 1)

        if len(fragments) == 1:
            return fragments[0], 'main'

        if len(fragments) == 2:
            return fragments[0], fragments[1]

        return None, None

    @classmethod
    def _load_module(cls, descriptor, module_name):
        # Load package
        try:
            fp, filename, (suffix, mode, type) = imp.find_module(
                descriptor['package_name'],
                [descriptor['root_path']]
            )
        except Exception as ex:
            log.warn('Unable to find package %r - %s', descriptor['package_name'], ex, exc_info=True)
            return None

        if type != imp.PKG_DIRECTORY:
            log.warn('Invalid package at %r (expected python package)', descriptor['package_path'])
            return None

        try:
            package = imp.load_module(descriptor['package_name'], fp, filename, (suffix, mode, type))
        except Exception as ex:
            log.warn('Unable to load package %r - %s', descriptor['package_name'], ex, exc_info=True)
            return None

        # Load module
        try:
            fp, filename, (suffix, mode, type) = imp.find_module(module_name, package.__path__)
        except Exception as ex:
            log.warn('Unable to find module %r in %r - %s', module_name, package.__name__, ex)
            return None

        if type not in [imp.PY_SOURCE, imp.PY_COMPILED]:
            log.warn('Invalid module at %r (expected python source or compiled module)', descriptor['module_path'])
            return None

        name = descriptor['package_name'] + '.' + module_name

        try:
            module = imp.load_module(name, fp, filename, (suffix, mode, type))
        except Exception as ex:
            log.warn('Unable to load module %r - %s', name, ex, exc_info=True)
            return None

        return module

    @classmethod
    def _list_plugins(cls):
        for package_path in cls.search_paths + sys.path:
            # Ignore invalid paths
            if package_path.endswith('.dist-info') or package_path.endswith('.egg') or \
               package_path.endswith('.egg-info') or package_path.endswith('.zip'):
                continue

            if not os.path.exists(package_path) or os.path.isfile(package_path):
                continue

            # Check if `package_path` is a plugin
            package_name = os.path.basename(package_path)

            if cls._is_plugin(package_name):
                # Find module
                name, descriptor = cls._find_plugin(package_name, package_path)

                if descriptor is None:
                    continue

                yield name, descriptor

            # List items in `package_path`
            try:
                items = os.listdir(package_path)
            except Exception as ex:
                log.debug('Unable to list directory %r - %s', package_path, ex, exc_info=True)
                continue

            # Find valid plugins in `items`
            for name in items:
                path = os.path.join(package_path, name)

                # Ignore invalid paths
                if path.endswith('.dist-info') or path.endswith('.egg') or \
                   path.endswith('.egg-info') or path.endswith('.zip'):
                    continue

                if cls._is_plugin(name) and path.endswith('.egg-link'):
                    name, path = cls._parse_link(path)

                    # Ensure package had been found
                    if not path:
                        continue
                else:
                    # Ignore files
                    if os.path.isfile(path):
                        continue

                    # Ensure package name matches a valid plugin prefix
                    if not cls._is_plugin(name):
                        continue

                # Find module
                module_name, descriptor = cls._find_plugin(name, path)

                if descriptor is None:
                    log.debug('No descriptor returned for %r (path: %r)', name, path)
                    continue

                yield module_name, descriptor

    @classmethod
    def _parse_link(cls, path):
        with open(path, 'r') as fp:
            package_path = fp.readline().strip()

        if not package_path:
            log.warn('Link has no path defined (link: %r)', path)
            return None, None

        try:
            items = os.listdir(package_path)
        except Exception as ex:
            log.warn('Unable to list directory %r (link: %r)', package_path, path)
            return None, None

        for name in items:
            path = os.path.join(package_path, name)

            # Ignore files
            if os.path.isfile(path):
                continue

            # Ensure package name matches a valid plugin prefix
            if cls._is_plugin(name):
                return name, path

        log.warn('Unable to find plugin module in %r (link: %r)', package_path, path)
        return None, None

    @classmethod
    def _find_plugin(cls, name, path):
        if not name:
            return None, None

        if cls._is_plugin_module(name):
            return name.replace('_', '-'), {
                'root_path': os.path.abspath(os.path.join(path, '..')),

                'package_path': path,
                'package_name': name
            }

        if cls._is_plugin_package(name):
            module_name = name.replace('-', '_')
            module_path = os.path.join(path, module_name)

            if not os.path.exists(module_path):
                return None, None

            return name, {
                'root_path': path,

                'package_path': module_path,
                'package_name': module_name
            }

        log.warn('Unknown plugin name: %r', name)
        return None, None

    @classmethod
    def _parse_package_name(cls, name):
        if not name:
            return None, None

        fragments = name.split('-', 2)

        if fragments[0] != 'oem':
            return None, None

        if len(fragments) < 3:
            return None, None

        return fragments[1], fragments[2]

    @classmethod
    def _is_plugin(cls, name):
        return cls._is_plugin_module(name) or cls._is_plugin_package(name)

    @classmethod
    def _is_plugin_module(cls, name):
        for prefix in MODULE_PREFIXES:
            if name.startswith(prefix):
                return True

        return False

    @classmethod
    def _is_plugin_package(cls, name):
        for prefix in PACKAGE_PREFIXES:
            if name.startswith(prefix):
                return True

        return False

    @staticmethod
    def _insert_plugin(a, x, lo=0, hi=None, key=None):
        if lo < 0:
            raise ValueError('lo must be non-negative')

        if hi is None:
            hi = len(a)

        if key is None:
            key = lambda x: x.__priority__

        while lo < hi:
            mid = (lo+hi)//2

            if key(a[mid]) < key(x):
                lo = mid+1
            else:
                hi = mid

        a.insert(lo, x)
