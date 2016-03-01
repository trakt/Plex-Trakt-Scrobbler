from ..common.utils import struct_parse, parse_cstring_from_stream
from .arch import Tags
from .sections import Section


class Attribute(object):
    def __init__(self, tag_id, raw, elf):
        self._elf = elf

        self.tag_id = tag_id

        self.raw = raw
        self.raw_type = type(raw)

        # Parse attribute
        self.tag = Tags.name(tag_id, elf.header.e_machine)
        self.value = Tags.value(self.tag, raw, elf.header.e_machine)


class AttributesSection(Section):
    def __init__(self, header, name, stream, elf):
        super(AttributesSection, self).__init__(header, name, stream)

        self._elf = elf
        self._structs = self._elf.structs

        self._offset = self['sh_offset'] + 1

        # Seek stream to offset
        self.stream.seek(self._offset)

        # Read attribute header
        self.attr_len = self._structs.Elf_word('attr_len').parse_stream(self.stream)
        self._offset += 4

        # Calculate end position
        self._end = self['sh_offset'] + self.attr_len

        # Read section name
        self.name = parse_cstring_from_stream(self.stream, self._offset)
        self._offset += len(self.name) + 2

    def get_attribute(self):
        # Seek stream
        self.stream.seek(self._offset)

        # Read attribute size
        size = self._structs.Elf_word('at_size').parse_stream(self.stream)

        if size < self.attr_len:
            self._offset += 4
        else:
            self.stream.seek(self._offset)
            size = None

        # Read attribute tag
        tag = self._structs.Elf_byte('at_key').parse_stream(self.stream)
        self._offset += 1

        if size:
            value = parse_cstring_from_stream(self.stream)
            self._offset += len(value) + 1
        else:
            value = self._structs.Elf_byte('at_value').parse_stream(self.stream)
            self._offset += 1

        return Attribute(tag, value, self._elf)

    def iter_attributes(self):
        while self._offset < self._end:
            yield self.get_attribute()
