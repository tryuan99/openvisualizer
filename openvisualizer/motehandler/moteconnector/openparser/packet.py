"""The packet defines different packet types."""

from openvisualizer.motehandler.moteconnector.openparser.struct_py import Struct, StructFieldType
from collections import OrderedDict


class UdpHeader(Struct):
    """UDP header."""

    @classmethod
    def fields(cls):
        """Returns a dictionary mapping each field name to its size in bytes,
        the array length, and an optional struct.
        """
        return OrderedDict([
            ("source_port", (StructFieldType.UINT16, 1)),
            ("destination_port", (StructFieldType.UINT16, 1)),
            ("length", (StructFieldType.UINT16, 1)),
            ("crc", (StructFieldType.UINT16, 1)),
        ])


class SensorNetworkPayload(Struct):
    """Sensor network payload.

    The sensor network payload is equivalent to the UDP paylod of a sensor
    network packet.
    """

    @classmethod
    def fields(cls):
        """Returns a dictionary mapping each field name to its size in bytes,
        the array length, and an optional struct.
        """
        return OrderedDict([
            ("source_address", (StructFieldType.UINT16, 1)),
            ("sequence_number", (StructFieldType.UINT8, 1)),
            ("channel", (StructFieldType.UINT8, 1)),
            ("reserved1", (StructFieldType.UINT8, 1)),
            ("reserved2", (StructFieldType.UINT8, 1)),
            ("output", (StructFieldType.UINT32, 8)),
            ("coarse", (StructFieldType.UINT8, 1)),
            ("mid", (StructFieldType.UINT8, 1)),
            ("fine", (StructFieldType.UINT8, 1)),
            ("reserved3", (StructFieldType.UINT8, 1)),
            ("crc", (StructFieldType.UINT16, 1)),
        ])


class SensorNetworkPacket(Struct):
    """Sensor network packet."""

    @classmethod
    def fields(cls):
        """Returns a dictionary mapping each field name to its size in bytes,
        the array length, and an optional struct.
        """
        return OrderedDict([
            ("udp_header", (StructFieldType.STRUCT, 1, UdpHeader)),
            ("udp_payload", (StructFieldType.STRUCT, 1, SensorNetworkPayload)),
        ])
