import sys

PY2 = sys.version_info[0] == 2
PY3 = sys.version_info[0] == 3

if PY3:
    def u(s):
        return s
else:
    def u(s):
        return unicode(s.replace(r'\\', r'\\\\'), "unicode_escape")
