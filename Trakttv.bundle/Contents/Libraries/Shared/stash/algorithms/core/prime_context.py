from stash.lib.six.moves import _thread


class PrimeContext(object):
    def __init__(self, algorithm=None, buffer=None):
        self._algorithm = algorithm
        self._buffer = buffer

    @property
    def buffer(self):
        return self._buffer

    def __enter__(self):
        if self._algorithm is None:
            return

        self._algorithm._buffers[_thread.get_ident()] = self._buffer

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._algorithm is None:
            return

        try:
            del self._algorithm._buffers[_thread.get_ident()]
        except KeyError:
            pass
