from plugin.core.environment import Environment

import os


CONTENTS_PATH = os.path.abspath(os.path.join(Environment.path.code, '..'))

NATIVE_DIRECTORIES = [
    'Libraries/FreeBSD',
    'Libraries/Linux',
    'Libraries/MacOSX',
    'Libraries/Windows'
]

UNICODE_MAP = {
    65535:      'ucs2',
    1114111:    'ucs4'
}
