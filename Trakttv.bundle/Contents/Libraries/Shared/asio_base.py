import time

DEFAULT_BUFFER_SIZE = 4096


SEEK_ORIGIN_BEGIN = 0
SEEK_ORIGIN_CURRENT = 1
SEEK_ORIGIN_END = 2


class ReadTimeoutError(Exception):
    pass


class BaseASIO(object):
    @classmethod
    def open(cls, file_path, parameters=None):
        raise NotImplementedError()

    @classmethod
    def get_size(cls, fp):
        raise NotImplementedError()

    @classmethod
    def get_path(cls, fp):
        raise NotImplementedError()

    @classmethod
    def seek(cls, fp, pointer, distance):
        raise NotImplementedError()

    @classmethod
    def read(cls, fp, buf_size=DEFAULT_BUFFER_SIZE):
        raise NotImplementedError()

    @classmethod
    def close(cls, fp):
        raise NotImplementedError()


class BaseFile(object):
    platform_handler = None

    def get_handler(self):
        """
        :rtype: BaseASIO
        """
        if not self.platform_handler:
            raise ValueError()

        return self.platform_handler

    def get_size(self):
        """Get the current file size

        :rtype: int
        """
        return self.get_handler().get_size(self)

    def get_path(self):
        """Get the path of this file

        :rtype: str
        """
        return self.get_handler().get_path(self)

    def seek(self, offset, origin):
        """Sets a reference point of a file to the given value.

        :param offset: The point relative to origin to move
        :type offset: int

        :param origin: Reference point to seek (SEEK_ORIGIN_BEGIN, SEEK_ORIGIN_CURRENT, SEEK_ORIGIN_END)
        :type origin: int
        """
        return self.get_handler().seek(self, offset, origin)

    def read(self, buf_size=DEFAULT_BUFFER_SIZE):
        """Read a block of characters from the file

        :type buf_size: int
        :rtype: str
        """
        return self.get_handler().read(self, buf_size)

    def read_line(self, timeout=None, timeout_type='exception'):
        """Read a single line from the file

        :rtype: str
        """

        stale_since = None
        line_buf = ""

        while not len(line_buf) or line_buf[-1] != '\n':
            ch = self.read(1)

            if not ch:
                if timeout:
                    # Check if we have exceeded the timeout
                    if stale_since and (time.time() - stale_since) > timeout:
                        # Timeout occurred, return the specified result
                        if timeout_type == 'exception':
                            raise ReadTimeoutError()
                        elif timeout_type == 'return':
                            return None
                        else:
                            raise ValueError('Unknown timeout_type "%s"' % timeout_type)

                    # Update stale_since when we hit 'None' reads
                    if not stale_since:
                        stale_since = time.time()

                continue
            elif timeout:
                # Reset stale_since as we received a character
                stale_since = None

            line_buf += ch

        return line_buf[:-1]

    def close(self):
        """Close the file handle"""
        return self.get_handler().close(self)
