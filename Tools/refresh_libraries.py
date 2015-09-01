from subprocess import call
import os
import shutil

BASE_PATH = os.path.join('Trakttv.bundle', 'Contents', 'Libraries', 'Shared')

DELETE_DIRECTORIES = [
    'futures',

    os.path.join('croniter', 'tests'),
    os.path.join('shove', 'tests'),
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
    'pwiz.py',
    'setup.py'
]

DELETE_EXTENSIONS = [
    '.pyd'
]


def install():
    call([
        "pip", "install",
        "--no-compile",
        "--no-deps",
        "--upgrade",
        "-r", os.path.join(BASE_PATH, 'requirements.txt'),
        "-t", os.path.join(BASE_PATH, '')
    ])


def compact():
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


if __name__ == '__main__':
    print "Installing libraries..."
    install()

    print "Compacting libraries..."
    compact()
