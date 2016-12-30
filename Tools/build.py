from git import Repo
from zipfile import ZipFile
import json
import os
import shutil
import zipfile


BUNDLE_NAME = 'Trakttv.bundle'
RELEASE_NAME = 'trakt_for_plex'

EXCLUDE_EXTENSIONS = [
    '.dist-info',
    '.egg-info',
    '.iml',
    '.pyc'
]

EXCLUDE_PATHS = [
    # Directories
    os.path.join('Contents', '.cache'),
    os.path.join('Contents', 'Tests'),

    # Files
    os.path.join('Contents', '.coveragerc'),
    os.path.join('Contents', '.version'),
    os.path.join('Contents', 'distribution.json'),
    os.path.join('Contents', 'setup.cfg'),
]

PLATFORMS = {
    'universal':        None,

    # Android
    'android_aarch64':  ('Android', 'aarch64'),

    # FreeBSD
    'freebsd_i386':     ('FreeBSD', 'i386'),
    'freebsd_x86_64':   ('FreeBSD', 'x86_64'),

    # Linux
    'linux_aarch64':    ('Linux', 'aarch64'),
    'linux_armv5':      ('Linux', ['armv5_hf', 'armv5_sf']),
    'linux_armv6':      ('Linux', ['armv6_hf', 'armv6_sf']),
    'linux_armv7':      ('Linux', ['armv7_hf', 'armv7_sf']),
    'linux_i386':       ('Linux', 'i386'),
    'linux_ppc':        ('Linux', 'PowerPC'),
    'linux_x86_64':     ('Linux', 'x86_64'),

    # Mac OSX
    'macosx_intel':     ('MacOSX', 'i386'),
    'macosx_x86_64':    ('MacOSX', 'x86_64'),

    # Windows
    'win32':            ('Windows', 'i386')
}


class Builder(object):
    def __init__(self, bundle_path, build_path, dist_path):
        self.bundle_path = bundle_path
        self.build_path = build_path
        self.dist_path = dist_path

    def run(self):
        print('bundle_path: %r' % self.bundle_path)
        print('build_path: %r' % self.build_path)
        print

        # Ensure bundle exists
        if not os.path.exists(self.bundle_path):
            return False

        # Ensure build directory exists
        if not os.path.exists(self.build_path):
            os.makedirs(self.build_path)

        # Build each platform
        for name, libraries in PLATFORMS.items():
            if not self.run_one(name, libraries):
                print('ERROR: build failed for %r', name)
                break

            print

    def run_one(self, name, libraries):
        system, arch = libraries if type(libraries) is tuple and len(libraries) == 2 else (None, None)

        print('Building platform "%s" (system: %r, arch: %r)...' % (name, system, arch))
        build_path = os.path.join(self.build_path, name)

        # Delete existing build directory
        if os.path.exists(build_path):
            shutil.rmtree(build_path)

        # Create new directory
        os.makedirs(build_path)

        # Copy bundle to build directory (and filter libraries)
        if not self.copy_bundle(build_path, system, arch):
            return False

        # Write platform metadata
        if not self.write_metadata(build_path, name, system, arch):
            return False

        # Compress bundle
        if not self.compress(build_path, name):
            return False

        print(' - Done')
        return True

    def copy_bundle(self, build_path, system, arch):
        def ignore(path, names):
            path = os.path.normpath(path)
            relative_path = os.path.relpath(path, self.bundle_path)

            if path.endswith(os.path.join('Contents', 'Libraries')):
                ignored = [
                    name for name in names
                    if type(system) is str and name != 'Shared' and name != system
                ]

                print(' - Applied system filter, ignored: %r' % ignored)
            elif system is not None and path.endswith(os.path.join('Contents', 'Libraries', system)):
                ignored = [
                    name for name in names
                    if (type(arch) is list and name not in arch) or (type(arch) is str and name != arch)
                ]

                print(' - Applied architecture filter, ignored: %r' % ignored)
            else:
                ignored = [
                    name for name in names
                    if (
                        os.path.join(relative_path, name) in EXCLUDE_PATHS or
                        os.path.splitext(name)[1] in EXCLUDE_EXTENSIONS
                    )
                ]

            return ignored

        print(' - Copying bundle to build directory...')
        shutil.copytree(
            self.bundle_path, os.path.join(build_path, BUNDLE_NAME),
            ignore=ignore
        )

        return True

    @classmethod
    def write_metadata(cls, build_path, name, system, arch):
        print(' - Writing metadata...')

        # Find bundle version + branch
        version, branch = cls.get_version(build_path)

        if not version or not branch:
            return False

        # Retrieve current commit
        commit = cls.get_current_commit()

        # Build metadata
        metadata = {
            'name': name,

            'release': {
                'version': version,
                'branch': branch
            },

            'system': system,
            'architectures': [arch] if type(arch) is str else arch
        }

        if commit:
            metadata['release']['commit'] = {
                'sha': commit.hexsha
            }

        # Build metadata path
        metadata_path = os.path.join(build_path, BUNDLE_NAME, 'Contents', 'distribution.json')

        # Write metadata to file
        with open(metadata_path, 'w') as fp:
            json.dump(metadata, fp)

        return True

    def compress(self, build_path, name):
        # Find bundle version + branch
        version, branch = self.get_version(build_path)

        if not version or not branch:
            return False

        # Retrieve current commit
        sha = self.get_current_sha()

        if not sha:
            return False

        # Build release name
        filename = '%s.zip' % ('-'.join([
            RELEASE_NAME,
            version,
            sha,
            name
        ]))

        print(' - Compressing package (filename: %r)...' % filename)

        # Ensure dist directory exists
        if not os.path.exists(self.dist_path):
            os.makedirs(self.dist_path)

        # Create distribution directory
        dist_directory = os.path.join(self.dist_path, version + '-' + sha)

        if not os.path.exists(dist_directory):
            os.mkdir(dist_directory)

        # Build distribution path
        dist_path = os.path.join(dist_directory, filename)

        # Remove existing distribution
        if os.path.exists(dist_path):
            os.remove(dist_path)

        # Create archive of bundle
        archive = ZipFile(dist_path, 'w', zipfile.ZIP_DEFLATED)

        for root, dirs, files in os.walk(build_path):
            for file in files:
                archive.write(
                    os.path.join(root, file),
                    os.path.join(os.path.relpath(root, build_path), file)
                )

        archive.close()
        return True

    @staticmethod
    def get_version(build_path):
        path = os.path.join(build_path, BUNDLE_NAME, 'Contents', 'Libraries', 'Shared', 'plugin', 'core', 'constants.py')

        # Ensure constants file exists
        if not os.path.exists(path):
            return None, None

        # Retrieve version constants
        with open(path, 'r') as fp:
            data = fp.read()

        data = '\n'.join([
            line.strip() for line in data.split('\n')
            if line.startswith('PLUGIN_VERSION_')
        ])

        # Evaluate python lines
        result = {}
        exec(data, {"__builtins__":None}, result)

        # Ensure result is valid
        version_base = result.get('PLUGIN_VERSION_BASE')
        version_branch = result.get('PLUGIN_VERSION_BRANCH')

        if not version_base or not version_branch:
            return None, None

        return (
            '.'.join([str(x) for x in version_base]),
            version_branch
        )

    @staticmethod
    def get_current_commit():
        repo = Repo(os.curdir)

        if not repo or repo.is_dirty():
            return None

        # Retrieve latest commit
        return repo.head.commit

    @staticmethod
    def get_current_sha():
        repo = Repo(os.curdir)

        if not repo:
            return None

        if repo.is_dirty():
            return 'dirty'

        # Retrieve latest commit
        commit = repo.head.commit

        if not commit or not commit.hexsha:
            return None

        return commit.hexsha[:7]


if __name__ == '__main__':
    Builder(
        bundle_path=os.path.abspath(BUNDLE_NAME),
        build_path=os.path.abspath('.build'),
        dist_path=os.path.abspath('dist')
    ).run()
