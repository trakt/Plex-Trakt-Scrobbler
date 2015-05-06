class Core(object):
    def __init__(self, code_path):
        self._code_path = code_path

    @property
    def code_path(self):
        return self._code_path
