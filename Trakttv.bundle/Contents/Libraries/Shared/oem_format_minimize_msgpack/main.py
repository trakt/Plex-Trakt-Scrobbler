from oem_format_minimize.main import MinimalFormat
from oem_format_msgpack.main import MessagePackFormat


class MessagePackMinimalFormat(MessagePackFormat, MinimalFormat):
    __key__ = 'minimize+msgpack'

    __extension__ = 'min.mpack'
