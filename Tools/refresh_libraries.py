from subprocess import call
import os
import shutil

BASE_PATH = os.path.join('Trakttv.bundle', 'Contents', 'Libraries', 'Shared')

DELETE_DIRECTORIES = [
    'futures',

    os.path.join('croniter', 'tests'),
    os.path.join('enum', 'doc'),
    os.path.join('ndg', 'httpsclient', 'test'),
    os.path.join('OpenSSL', 'test'),
    os.path.join('shove', 'tests'),
    os.path.join('tzlocal', 'test_data'),
    os.path.join('websocket', 'tests'),
    'tests',

    os.path.join('raven', 'contrib', 'bottle'),
    os.path.join('raven', 'contrib', 'celery'),
    os.path.join('raven', 'contrib', 'django'),
    os.path.join('raven', 'contrib', 'pylons'),
    os.path.join('raven', 'contrib', 'tornado'),
    os.path.join('raven', 'contrib', 'webpy'),
    os.path.join('raven', 'contrib', 'zerorpc'),
    os.path.join('raven', 'contrib', 'zope')
]

DELETE_FILES = [
    os.path.join('enum', 'README'),
    os.path.join('enum', 'enum.py'),
    os.path.join('enum', 'py35_test_enum.py'),
    os.path.join('enum', 'test.py'),
    os.path.join('tzlocal', 'tests.py'),

    'ndg_httpsclient-0.4.0-py2.7-nspkg.pth',
    'pwiz.py',
    'setup.py'
]

DELETE_EXTENSIONS = [
    '.pth',
    '.pyd'
]


def run_install():
    call([
        "pip", "install",
        "--no-compile",
        "--no-deps",
        "--upgrade",
        "-r", os.path.join(BASE_PATH, 'requirements.txt'),
        "-t", os.path.join(BASE_PATH, '')
    ])


def run_compact():
    # Delete directories
    for path in DELETE_DIRECTORIES:
        try:
            shutil.rmtree(os.path.join(BASE_PATH, path))
            print "Deleted directory: %r" % path
        except Exception, ex:
            print "Unable to delete directory: %r - %s" % (path, ex)

    # Delete files
    for name in DELETE_FILES:
        path = os.path.join(BASE_PATH, name)

        try:
            os.remove(path)
            print "Deleted file: %r" % path
        except Exception, ex:
            print "Unable to delete file: %r - %s" % (path, ex)

    # Delete extensions
    for root, _, files in os.walk(BASE_PATH):
        for name in files:
            _, ext = os.path.splitext(name)

            if ext in DELETE_EXTENSIONS:
                path = os.path.join(root, name)

                try:
                    os.remove(path)
                    print "Deleted file: %r" % path
                except Exception, ex:
                    print "Unable to delete file: %r - %s" % (path, ex)


def run_extras():
    # Create "ndg/__init__.py" file
    touch(os.path.join('ndg', '__init__.py'))

    # Delete "*.dist-info" "*.egg-info" directories
    for name in os.listdir(BASE_PATH):
        if not name.endswith('.dist-info') and not name.endswith('.egg-info'):
            continue

        path = os.path.join(BASE_PATH, name)

        try:
            shutil.rmtree(path)
            print "Deleted directory: %r" % path
        except Exception, ex:
            print "Unable to delete directory: %r - %s" % (path, ex)


def write(path, content):
    path = os.path.join(BASE_PATH, path)

    with open(path, 'wb') as fp:
        fp.write(content)


def touch(path):
    return write(path, '')


if __name__ == '__main__':
    print "Installing libraries..."
    run_install()

    print "Compacting libraries..."
    run_compact()

    print "Running extra tasks on libraries..."
    run_extras()
