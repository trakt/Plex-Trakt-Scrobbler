import sys


class NullWriter(object):
    def write(self, value):
        pass

# Redirect standard streams to the `NullWriter`
sys.stdout = sys.stderr = NullWriter()
