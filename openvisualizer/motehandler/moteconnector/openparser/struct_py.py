"""The struct imitates the functionality of a C-style struct in Python."""

import struct
from abc import abstractmethod
from collections import OrderedDict

class StructFieldEndianness:
    """Struct field endianness enumeration."""
    LITTLE_ENDIAN = 0
    BIG_ENDIAN = 1


# Map from the struct field endianness to its format string.
STRUCT_FIELD_ENDIANNESS_TO_FORMAT_STRING = {
    StructFieldEndianness.LITTLE_ENDIAN: "<",
    StructFieldEndianness.BIG_ENDIAN: ">",
}


class StructFieldType:
    """Struct field type enumeration."""
    CHAR = 0
    BOOL = 1
    INT8 = 2
    UINT8 = 3
    INT16 = 4
    UINT16 = 5
    INT32 = 6
    UINT32 = 7
    INT64 = 8
    UINT64 = 9
    FLOAT = 10
    DOUBLE = 11
    STRUCT = 12
    UNION = 13


# Map from the struct field type to its size in bytes.
STRUCT_FIELD_TYPE_TO_SIZE = {
    StructFieldType.CHAR: 1,
    StructFieldType.BOOL: 1,
    StructFieldType.INT8: 1,
    StructFieldType.UINT8: 1,
    StructFieldType.INT16: 2,
    StructFieldType.UINT16: 2,
    StructFieldType.INT32: 4,
    StructFieldType.UINT32: 4,
    StructFieldType.INT64: 8,
    StructFieldType.UINT64: 8,
    StructFieldType.FLOAT: 4,
    StructFieldType.DOUBLE: 8,
}

# Map from the struct field type to its format character.
STRUCT_FIELD_TYPE_TO_FORMAT_CHAR = {
    StructFieldType.CHAR: "c",
    StructFieldType.BOOL: "?",
    StructFieldType.INT8: "b",
    StructFieldType.UINT8: "B",
    StructFieldType.INT16: "h",
    StructFieldType.UINT16: "H",
    StructFieldType.INT32: "i",
    StructFieldType.UINT32: "I",
    StructFieldType.INT64: "q",
    StructFieldType.UINT64: "Q",
    StructFieldType.FLOAT: "f",
    StructFieldType.DOUBLE: "d",
}


class Struct:
    """Interface for a C-style struct.

    Attributes:
        buffer: Data bytearray or bytes.
        endian: Endianness of the bytearray.
    """

    def __init__(
        self,
        buffer=None,
        endian=StructFieldEndianness.LITTLE_ENDIAN,
    ):
        if buffer is not None:
            self.buffer = bytearray(buffer)
        else:
            self.buffer = bytearray(self.size())
        self.endian = endian

    @classmethod
    def union(cls):
        """Returns whether the struct is a union."""
        return False

    @classmethod
    @abstractmethod
    def fields(cls):
        """Returns a dictionary mapping each field name to its size in bytes,
        the array length, and an optional struct.

        If the field type is a basic data type, the extra argument is unused.
        If the field type is a struct or a union, the extra argument is a struct.
        Anonymous structs or unions are not supported.
        """

    @classmethod
    def size(cls):
        """Returns the size of the struct."""
        offsets, size = Struct._calculate_offsets(cls.fields(), cls.union())
        return size

    @classmethod
    def offsets(cls):
        """Returns a dictionary mapping each field name to its byte offset."""
        offsets, size = Struct._calculate_offsets(cls.fields(), cls.union())
        return offsets

    def get(self, field, index=None):
        """Accesses the specified struct field.

        Args:
            field: Field name.
            index: Optional index for arrays.

        Returns:
            The value associated with the field. If the field is an array and
            no index is specified, returns a list of values.

        Raises:
            ValueError: If the field does not exist.
        """
        if field not in self.fields():
            raise ValueError("Field {0} does not exist.".format(field))
        if len(self.fields()[field]) == 3:
            field_type, num_elements, struct_cls = self.fields()[field]
        else:
            field_type, num_elements = self.fields()[field]
            struct_cls = None
        field_size = Struct._calculate_size(field_type, struct_cls)
        offset = self.offsets()[field]

        if num_elements == 1:
            return self._get_single_element(field, offset)
        if index is not None:
            return self._get_single_element(field, offset + field_size * index)
        return [
            self._get_single_element(field, offset + field_size * i)
            for i in range(num_elements)
        ]

    def get_buffer(self, start=None, end=None):
        """Returns the bytearray between the start and end indices.

        If no start index is provided, the bytearray from the beginning of the
        buffer will be returned. If no end is provided, the bytearray until the
        end of the buffer will be returned.

        Args:
            start: Start index.
            end: End index.
        """
        if start is None:
            start = 0
        if end is None:
            end = len(self.buffer)
        return self.buffer[start:end]

    def set(self, field, value, index=None):
        """Sets the specified struct field.

        If the field is an array, either the entire array or the element at a
        specific index can be set.

        Args:
            field: Field name.
            value: Value to set.
            index: Optional index for arrays.

        Raises:
            ValueError: If the field does not exist.
        """
        if field not in self.fields():
            raise ValueError("Field {0} does not exist.".format(field))
        if len(self.fields()[field]) == 3:
            field_type, num_elements, struct_cls = self.fields()[field]
        else:
            field_type, num_elements = self.fields()[field]
            struct_cls = None
        field_size = Struct._calculate_size(field_type, struct_cls)
        offset = self.offsets()[field]

        if num_elements == 1:
            self._set_single_element(field, offset, value)
        elif index is not None:
            self._set_single_element(field, offset + field_size * index, value)
        else:
            for i in range(num_elements):
                self._set_single_element(field, offset + field_size * i,
                                         value[i])

    def set_buffer(self, data, start=None):
        """Sets the bytearray from the start index.

        If no start index is provided, the bytearray will be set from the
        beginning of the buffer.

        Args:
            data: Data to set.
            start: Start index.
        """
        if start is None:
            start = 0
        self.buffer[start:start + len(data)] = data

    @staticmethod
    def _calculate_offsets(fields, union):
        """Returns a 2-tuple consisting of a dictionary mapping each field name
        to its byte offset and the total struct size.

        Args:
            field: Struct fields.
            union: If true, the struct is a union.
        """
        offsets = {}
        offset = 0
        max_field_size = 0
        for field, field_tuple in fields.items():
            if len(field_tuple) == 3:
                field_type, num_elements, struct_cls = field_tuple
            else:
                field_type, num_elements = field_tuple
                struct_cls = None
            offsets[field] = offset
            field_size = Struct._calculate_size(field_type, struct_cls)
            max_field_size = max(max_field_size, field_size)
            if not union:
                offset += field_size * num_elements
        size = offset if not union else max_field_size
        return offsets, size

    @staticmethod
    def _calculate_size(field_type, struct_cls):
        """Returns the size of the given field type.

        Args:
            field_type: Field type.
            struct_cls: Nested struct or union.
        """
        if field_type == StructFieldType.STRUCT or field_type == StructFieldType.UNION:
            return struct_cls.size()
        return STRUCT_FIELD_TYPE_TO_SIZE[field_type]

    def _get_single_element(self, field, offset):
        """Returns the single value at the specified offset.

        Args:
            field: Field name.
            offset: Byte offset within the buffer.
        """
        if len(self.fields()[field]) == 3:
            field_type, num_elements, struct_cls = self.fields()[field]
        else:
            field_type, num_elements = self.fields()[field]
            struct_cls = None
        field_size = Struct._calculate_size(field_type, struct_cls)

        buffer = self.buffer[offset:offset + field_size]
        if field_type == StructFieldType.STRUCT or field_type == StructFieldType.UNION:
            return struct_cls(buffer, self.endian)
        endian_string = STRUCT_FIELD_ENDIANNESS_TO_FORMAT_STRING[self.endian]
        format_char = STRUCT_FIELD_TYPE_TO_FORMAT_CHAR[field_type]
        return struct.unpack("{0}{1}".format(endian_string, format_char),
                             buffer)[0]

    def _set_single_element(self, field, offset, value):
        """Sets the single value at the specified offset.

        Args:
            field: Field name.
            offset: Byte offset within the buffer.
            value: Value to set.
        """
        if len(self.fields()[field]) == 3:
            field_type, num_elements, struct_cls = self.fields()[field]
        else:
            field_type, num_elements = self.fields()[field]
            struct_cls = None
        field_size = Struct._calculate_size(field_type, struct_cls)

        if field_type == StructFieldType.STRUCT or field_type == StructFieldType.UNION:
            self.buffer[offset:offset + field_size] = value.get_buffer()
        else:
            endian_string = STRUCT_FIELD_ENDIANNESS_TO_FORMAT_STRING[
                self.endian]
            format_char = STRUCT_FIELD_TYPE_TO_FORMAT_CHAR[field_type]
            self.buffer[offset:offset + field_size] = struct.pack(
                "{0}{1}".format(endian_string, format_char), value)


class Union(Struct):
    """Interface for a C-style union."""

    @classmethod
    def union(cls):
        """Returns whether the struct is a union."""
        return True
