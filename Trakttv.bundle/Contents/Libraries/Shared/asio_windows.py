from asio_base import BaseASIO, BaseFile, DEFAULT_BUFFER_SIZE
from ctypes.wintypes import *
from ctypes import *


LPSECURITY_ATTRIBUTES = c_void_p
NULL = 0


class WindowsASIO(BaseASIO):
    @classmethod
    def open(cls, file_path, parameters=None):
        """
        :type file_path: str
        :rtype: WindowsFile
        """
        if not parameters:
            parameters = {}

        print parameters

        h = WindowsInterop.create_file(
            file_path,
            parameters.get('desired_access', WindowsASIO.DesiredAccess.READ),
            parameters.get('share_mode', WindowsASIO.ShareMode.ALL),
            parameters.get('creation_disposition', WindowsASIO.CreationDisposition.OPEN_EXISTING),
            parameters.get('flags_and_attributes', NULL)
        )

        error = GetLastError()
        if error != 0:
            raise Exception('[WindowsASIO.open] "%s"' % FormatError(error))

        return WindowsFile(h)

    @classmethod
    def size(cls, fp):
        """
        :type fp: WindowsFile:
        :rtype: int
        """
        return WindowsInterop.get_file_size(fp.handle)


    @classmethod
    def seek(cls, fp, offset, origin):
        """
        :type fp: WindowsFile
        :type offset: int
        :type origin: int
        :rtype: int
        """

        result = WindowsInterop.set_file_pointer(
            fp.handle,
            offset,
            origin
        )
        if result == -1:
            raise Exception('[WindowsASIO.seek] INVALID_SET_FILE_POINTER: "%s"' % FormatError(GetLastError()))

        return result

    @classmethod
    def read(cls, fp, buf_size=DEFAULT_BUFFER_SIZE):
        """
        :type fp: WindowsFile
        :type buf_size: int
        :rtype: str
        """
        success, buf = WindowsInterop.read_file(fp.handle, buf_size)
        if not success:
            return None

        return buf.value


    @classmethod
    def close(cls, fp):
        """
        :type fp: WindowsFile
        :rtype: bool
        """
        return bool(WindowsInterop.close_handle(fp.handle))

    class DesiredAccess(object):
        READ = 0x80000000
        WRITE = 0x40000000
        EXECUTE = 0x20000000
        ALL = 0x10000000

    class ShareMode(object):
        READ = 0x00000001
        WRITE = 0x00000002
        DELETE = 0x00000004
        ALL = READ | WRITE | DELETE

    class CreationDisposition(object):
        CREATE_NEW = 1
        CREATE_ALWAYS = 2
        OPEN_EXISTING = 3
        OPEN_ALWAYS = 4
        TRUNCATE_EXISTING = 5

    class Attribute(object):
        READONLY = 0x00000001
        HIDDEN = 0x00000002
        SYSTEM = 0x00000004
        DIRECTORY = 0x00000010
        ARCHIVE = 0x00000020
        DEVICE = 0x00000040
        NORMAL = 0x00000080
        TEMPORARY = 0x00000100
        SPARSE_FILE = 0x00000200
        REPARSE_POINT = 0x00000400
        COMPRESSED = 0x00000800
        OFFLINE = 0x00001000
        NOT_CONTENT_INDEXED = 0x00002000
        ENCRYPTED = 0x00004000

    class Flag(object):
        WRITE_THROUGH = 0x80000000
        OVERLAPPED = 0x40000000
        NO_BUFFERING = 0x20000000
        RANDOM_ACCESS = 0x10000000
        SEQUENTIAL_SCAN = 0x08000000
        DELETE_ON_CLOSE = 0x04000000
        BACKUP_SEMANTICS = 0x02000000
        POSIX_SEMANTICS = 0x01000000
        OPEN_REPARSE_POINT = 0x00200000
        OPEN_NO_RECALL = 0x00100000
        FIRST_PIPE_INSTANCE = 0x00080000


class WindowsFile(BaseFile):
    platform_handler = WindowsASIO

    def __init__(self, file_handle):
        super(WindowsFile, self).__init__(file_handle)


class WindowsInterop(object):
    @classmethod
    def create_file(cls, path, desired_access, share_mode, creation_disposition, flags_and_attributes):
        return HANDLE(windll.kernel32.CreateFileW(
            LPWSTR(path),
            DWORD(desired_access),
            DWORD(share_mode),
            LPSECURITY_ATTRIBUTES(NULL),
            DWORD(creation_disposition),
            DWORD(flags_and_attributes),
            HANDLE(NULL)
        ))

    @classmethod
    def read_file(cls, handle, buf_size=DEFAULT_BUFFER_SIZE):
        buf = create_string_buffer(buf_size)
        bytes_read = c_ulong(0)

        success = windll.kernel32.ReadFile(handle, buf, buf_size, byref(bytes_read), None)
        if not success or not bytes_read.value:
            return False, None

        return True, buf

    @classmethod
    def set_file_pointer(cls, handle, distance, method):
        pos_high = DWORD(NULL)

        return windll.kernel32.SetFilePointer(
            handle,
            c_ulong(distance),
            byref(pos_high),
            DWORD(method)
        )

    @classmethod
    def get_file_size(cls, handle):
        return windll.kernel32.GetFileSize(
            handle,
            DWORD(NULL)
        )

    @classmethod
    def close_handle(cls, handle):
        return windll.kernel32.CloseHandle(handle)
