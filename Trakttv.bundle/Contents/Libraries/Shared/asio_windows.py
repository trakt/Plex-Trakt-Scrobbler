from asio_base import BaseASIO, BaseFile, DEFAULT_BUFFER_SIZE
import os

if os.name == 'nt':
    from ctypes.wintypes import *
    from ctypes import *

    LPSECURITY_ATTRIBUTES = c_void_p

NULL = 0
MAX_PATH = 260


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
            parameters.get('desired_access', WindowsASIO.GenericAccess.READ),
            parameters.get('share_mode', WindowsASIO.ShareMode.ALL),
            parameters.get('creation_disposition', WindowsASIO.CreationDisposition.OPEN_EXISTING),
            parameters.get('flags_and_attributes', NULL)
        )

        error = GetLastError()
        if error != 0:
            raise Exception('[WindowsASIO.open] "%s"' % FormatError(error))

        return WindowsFile(h)

    @classmethod
    def get_size(cls, fp):
        """
        :type fp: WindowsFile:
        :rtype: int
        """
        return WindowsInterop.get_file_size(fp.handle)

    @classmethod
    def get_path(cls, fp):
        """
        :type fp: WindowsFile:
        :rtype: str
        """

        if not fp.file_map:
            fp.file_map = WindowsInterop.create_file_mapping(fp.handle, WindowsASIO.Protection.READONLY)

        if not fp.map_view:
            fp.map_view = WindowsInterop.map_view_of_file(fp.file_map, WindowsASIO.FileMapAccess.READ, 1)

        file_name = WindowsInterop.get_mapped_file_name(fp.map_view)

        return file_name

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
        
        error = GetLastError()
        if error != 0:
            print FormatError(error)

        if not success:
            return None

        return buf.value

    @classmethod
    def close(cls, fp):
        """
        :type fp: WindowsFile
        :rtype: bool
        """
        if fp.map_view:
            WindowsInterop.unmap_view_of_file(fp.map_view)

        if fp.file_map:
            WindowsInterop.close_handle(fp.file_map)

        return bool(WindowsInterop.close_handle(fp.handle))

    class GenericAccess(object):
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

    class Protection(object):
        NOACCESS = 0x01
        READONLY = 0x02
        READWRITE = 0x04
        WRITECOPY = 0x08
        EXECUTE = 0x10
        EXECUTE_READ = 0x20,
        EXECUTE_READWRITE = 0x40
        EXECUTE_WRITECOPY = 0x80
        GUARD = 0x100
        NOCACHE = 0x200
        WRITECOMBINE = 0x400

    class FileMapAccess(object):
        COPY = 0x0001
        WRITE = 0x0002
        READ = 0x0004
        ALL_ACCESS = 0x001f
        EXECUTE = 0x0020


class WindowsFile(BaseFile):
    platform_handler = WindowsASIO

    def __init__(self, handle):
        self.handle = handle

        self.file_map = None
        self.map_view = None

    def __str__(self):
        return "<asio_windows.WindowsFile file: %s>" % self.handle


class WindowsInterop(object):
    @classmethod
    def clean_buffer_value(cls, buf):
        value = ""

        for ch in buf.raw:
            if ord(ch) != 0:
                value += ch

        return value

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

    @classmethod
    def create_file_mapping(cls, handle, protect, maximum_size_high=0, maximum_size_low=1):
        return HANDLE(windll.kernel32.CreateFileMappingW(
            handle,
            LPSECURITY_ATTRIBUTES(NULL),
            DWORD(protect),
            DWORD(maximum_size_high),
            DWORD(maximum_size_low),
            LPCSTR(NULL)
        ))

    @classmethod
    def map_view_of_file(cls, map_handle, desired_access, num_bytes, file_offset_high=0, file_offset_low=0):
        return HANDLE(windll.kernel32.MapViewOfFile(
            map_handle,
            DWORD(desired_access),
            DWORD(file_offset_high),
            DWORD(file_offset_low),
            num_bytes
        ))

    @classmethod
    def unmap_view_of_file(cls, view_handle):
        return windll.kernel32.UnmapViewOfFile(view_handle)

    @classmethod
    def get_mapped_file_name(cls, view_handle, translate_device_name=True):
        buf = create_string_buffer(MAX_PATH + 1)

        result = windll.psapi.GetMappedFileNameW(
            cls.get_current_process(),
            view_handle,
            buf,
            MAX_PATH
        )

        # Raise exception on error
        error = GetLastError()
        if result == 0:
            raise Exception(FormatError(error))

        # Retrieve a clean file name (skipping over NUL bytes)
        file_name = cls.clean_buffer_value(buf)

        # If we are not translating the device name return here
        if not translate_device_name:
            return file_name

        drives = cls.get_logical_drive_strings()

        # Find the drive matching the file_name device name
        translated = False
        for drive in drives:
            device_name = cls.query_dos_device(drive)

            if file_name.startswith(device_name):
                file_name = drive + file_name[len(device_name):]
                translated = True
                break

        if not translated:
            raise Exception('Unable to translate device name')

        return file_name

    @classmethod
    def get_logical_drive_strings(cls, buf_size=512):
        buf = create_string_buffer(buf_size)

        result = windll.kernel32.GetLogicalDriveStringsW(buf_size, buf)

        error = GetLastError()
        if result == 0:
            raise Exception(FormatError(error))

        drive_strings = cls.clean_buffer_value(buf)
        return [dr for dr in drive_strings.split('\\') if dr != '']

    @classmethod
    def query_dos_device(cls, drive, buf_size=MAX_PATH):
        buf = create_string_buffer(buf_size)

        result = windll.kernel32.QueryDosDeviceA(
            drive,
            buf,
            buf_size
        )

        error = GetLastError()
        if result == 0:
            print Exception('%s (%s)' % (FormatError(error), error))

        return cls.clean_buffer_value(buf)

    @classmethod
    def get_current_process(cls):
        return HANDLE(windll.kernel32.GetCurrentProcess())
