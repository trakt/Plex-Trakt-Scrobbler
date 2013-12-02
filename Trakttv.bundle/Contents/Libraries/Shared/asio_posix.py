from asio_base import BaseASIO, DEFAULT_BUFFER_SIZE, BaseFile
import os

if os.name == 'posix':
    import fcntl
    import select


class PosixASIO(BaseASIO):
    @classmethod
    def open(cls, file_path, parameters=None):
        """
        :type file_path: str
        :rtype: PosixFile
        """
        if not parameters:
            parameters = {}

        if not parameters.get('mode'):
            parameters.pop('mode')

        if not parameters.get('buffering'):
            parameters.pop('buffering')

        print parameters

        fd = os.open(file_path, os.O_RDONLY | os.O_NONBLOCK)

        return PosixFile(fd)

    @classmethod
    def get_size(cls, fp):
        """
        :type fp: PosixFile
        :rtype: int
        """
        return os.fstat(fp.fd).st_size

    @classmethod
    def get_path(cls, fp):
        """
        :type fp: PosixFile
        :rtype: int
        """
        return os.readlink("/dev/fd/%s" % fp.fd)

    @classmethod
    def seek(cls, fp, offset, origin):
        """
        :type fp: PosixFile
        :type offset: int
        :type origin: int
        """
        os.lseek(fp.fd, offset, origin)

    @classmethod
    def read(cls, fp, buf_size=DEFAULT_BUFFER_SIZE):
        """
        :type fp: PosixFile
        :type buf_size: int
        :rtype: str
        """
        r, w, x = select.select([fp.fd], [], [], 5)

        if r:
            return os.read(fp.fd, buf_size)

        return None

    @classmethod
    def close(cls, fp):
        """
        :type fp: PosixFile
        """
        os.close(fp.fd)


class PosixFile(BaseFile):
    platform_handler = PosixASIO

    def __init__(self, fd):
        """
        :type file_object: FileIO
        """
        self.fd = fd

    def __str__(self):
        return "<asio_posix.PosixFile file: %s>" % self.fd
