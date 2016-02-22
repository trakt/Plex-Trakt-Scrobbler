from tests.helpers.io import touch
import plugin.core.importer as importer

import os
import shutil
import tempfile


# Create temporary directory
TEMP_DIR = tempfile.mkdtemp()


def test_get_name():
    base_path = os.path.join(TEMP_DIR, 'test_get_name')
    os.mkdir(base_path)

    # Ensure file name is built correctly
    assert get_name(base_path, 'file.py') == 'test.file'

    # Ensure directory name is built correctly
    assert get_name(base_path, 'directory', is_directory=True) == 'test.directory'

    # Remove test directory
    shutil.rmtree(base_path)


def test_is_module():
    base_path = os.path.join(TEMP_DIR, 'test_is_module')
    os.mkdir(base_path)

    # Ensure invalid paths are ignored
    assert is_module(base_path, 'does-not-exist') is False

    # Ensure directory passes
    assert is_module(base_path, 'directory', create='directory')

    # Ensure file passes
    assert is_module(base_path, 'file.py', create='file')

    # Remove test directory
    shutil.rmtree(base_path)


def test_is_module_directory():
    base_path = os.path.join(TEMP_DIR, 'test_is_module_directory')
    os.mkdir(base_path)

    # Ensure directories without "__init__.py" files are ignored
    assert is_module_directory(base_path, 'one', init_file=False) is False

    # Ensure files with a "." or "_" prefix are ignored
    assert is_module_directory(base_path, '.two') is False
    assert is_module_directory(base_path, '_three') is False

    # Ensure files with a "." suffix are ignored
    assert is_module_directory(base_path, 'four.') is False

    # Ensure valid directories pass
    assert is_module_directory(base_path, 'five') is True

    # Remove test directory
    shutil.rmtree(base_path)


def test_is_module_file():
    # Ensure files without the "*.py" extension are ignored
    assert importer.is_module_file('./compiled.pyc', 'compiled.pyc') is False
    assert importer.is_module_file('./misc.txt', 'misc.txt') is False

    # Ensure files with a "." or "_" prefix are ignored
    assert importer.is_module_file('./_invalid.py', '_invalid.py') is False
    assert importer.is_module_file('./.hidden.py', '.hidden.py') is False

    # Ensure files with a "." suffix are ignored
    assert importer.is_module_file('./hidden..py', 'hidden..py') is False

    # Ensure valid files pass
    assert importer.is_module_file('./valid.py', 'valid.py') is True
    assert importer.is_module_file('./valid_.py', 'valid_.py') is True
    assert importer.is_module_file('./valid_module.py', 'valid_module.py') is True


#
# Test helpers
#

def get_name(base_path, name, is_directory=False):
    path = os.path.join(base_path, name)

    if is_directory:
        # Create directory test
        os.makedirs(path)
    else:
        # Create file test
        touch(path)

    # Run `get_name()` function
    return importer.get_name(path, 'test', name)


def is_module(base_path, name, create=None, create_init_file=True):
    path = os.path.join(base_path, name)

    if create == 'directory':
        # Create directory test
        os.makedirs(path)

        if create_init_file:
            touch(os.path.join(path, '__init__.py'))
    elif create == 'file':
        # Create file test
        touch(path)

    # Run `is_module()` function
    return importer.is_module(path, name)


def is_module_directory(base_path, name, init_file=True):
    path = os.path.join(base_path, name)

    # Create directory
    os.mkdir(path)

    if init_file:
        # Create "__init__.py" file
        touch(os.path.join(path, '__init__.py'))

    # Run `is_module_directory()` function
    return importer.is_module_directory(path, name)
