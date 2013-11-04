from asio_base import SEEK_ORIGIN_CURRENT
from asio_windows import WindowsASIO
import os


class ASIO(object):
    platform_handler = None

    @classmethod
    def get_handler(cls):
        if cls.platform_handler:
            return cls.platform_handler

        if os.name == 'nt':
            cls.platform_handler = WindowsASIO
        else:
            raise NotImplementedError()

        return cls.platform_handler

    @classmethod
    def open(cls, file_path, opener=True, parameters=None):
        """Open file

        :type file_path: str

        :param opener: Use FileOpener, for use with the 'with' statement
        :type opener: bool

        :rtype: BaseFile
        """

        if opener:
            return FileOpener(file_path, parameters)

        return ASIO.get_handler().open(
            file_path,
            parameters=parameters.handlers.get(ASIO.get_handler())
        )


class OpenParameters(object):
    def __init__(self):
        self.handlers = {}

        # Update handler_parameters with defaults
        self.windows()

    def windows(self,
                desired_access=WindowsASIO.DesiredAccess.READ,
                share_mode=WindowsASIO.ShareMode.ALL,
                creation_disposition=WindowsASIO.CreationDisposition.OPEN_EXISTING,
                flags_and_attributes=0):

        """
        :param desired_access: WindowsASIO.DesiredAccess
        :type desired_access: int

        :param share_mode: WindowsASIO.ShareMode
        :type share_mode: int

        :param creation_disposition: WindowsASIO.CreationDisposition
        :type creation_disposition: int

        :param flags_and_attributes: WindowsASIO.Attribute, WindowsASIO.Flag
        :type flags_and_attributes: int
        """

        self.handlers.update({WindowsASIO: {
            'desired_access': desired_access,
            'share_mode': share_mode,
            'creation_disposition': creation_disposition,
            'flags_and_attributes': flags_and_attributes
        }})


class FileOpener(object):
    def __init__(self, file_path, parameters=None):
        self.file_path = file_path
        self.parameters = parameters

        self.file = None

    def __enter__(self):
        self.file = ASIO.get_handler().open(
            self.file_path,
            self.parameters.handlers.get(ASIO.get_handler())
        )

        return self.file

    def __exit__(self, exc_type, exc_val, exc_tb):
        if not self.file:
            return

        self.file.close()
        self.file = None

if __name__ == '__main__':
    path = "C:\\Users\\Gardi_000\\AppData\\Local\\Plex Media Server\\Logs\\Plex Media Server.log"

    params = OpenParameters()

    with ASIO.open(path, parameters=params) as f:
        print "Handle: %s" % f.handle

        size = f.size()
        print "Seeking to end, %s" % size
        print f.seek(size, SEEK_ORIGIN_CURRENT)

        while True:
            line = f.read_line(timeout=1, timeout_type='return')

            print line
