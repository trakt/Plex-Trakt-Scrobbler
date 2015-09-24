import os

TESTS_PATH = os.path.abspath(os.path.dirname(__file__) + os.path.sep + '..')


def read(*args):
    if not args:
        return None

    args = list(args)

    for x, component in enumerate(args):
        if not component.endswith('.py'):
            continue

        args[x] = os.path.dirname(component)

    path = os.path.join(*args)

    if not os.path.isabs(path):
        path = os.path.join(TESTS_PATH, path)

    path = os.path.abspath(path)

    with open(path, 'rb') as fp:
        return fp.read()
