from subprocess import call
import os
import shutil

BASE_PATH = 'Trakttv.bundle\Contents\Libraries\Shared'

DELETE_DIRECTORIES = [
    'futures',

    'croniter\\tests',
    'shove\\tests',
    'tests',

    'raven\\contrib\\bottle',
    'raven\\contrib\\celery',
    'raven\\contrib\\django',
    'raven\\contrib\\pylons',
    'raven\\contrib\\tornado',
    'raven\\contrib\\webpy',
    'raven\\contrib\\zerorpc',
    'raven\\contrib\\zope'
]

DELETE_FILES = [
    'pwiz.py'
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
        "-r", "Trakttv.bundle\\Contents\\Libraries\\Shared\\requirements.txt",
        "-t", "Trakttv.bundle\\Contents\\Libraries\\Shared\\"
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
