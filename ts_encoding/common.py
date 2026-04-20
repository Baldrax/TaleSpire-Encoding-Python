"""
Base TS Encoding classes and functions for use in the specific encoders.

URL Schemes are documented here:
https://talespire.com/url-scheme

Standard Byte order is little-endian
"""
import base64
import struct
import uuid


class TSCodingBase:
    """
    A Base Class to Decode and Encode a TaleSpire content.

    For Decoding:
    The class stores the binary data and an offset which represents the current position/index we are at in the
    binary data. Each unpack method then increments the offset by the proper amount so we can decode the next
    step without having to feed in the offset index.
    """

    def __init__(self):
        self.data = {}
        self._init_data()
        self._version = 0
        self._encode_version = 2
        self._code = None
        self._binary_data = None
        self._offset = 0

    def _init_data(self) -> None:
        """
        This is intended to be overridden by the subclass.
        The data dictionary should be initialized to a default state declaring all the data needed.
        """
        self.data = {
            "version": 1,
        }

    def _decode(self) -> None:
        """
        Preps self._code into self._binary_data then runs self._decode_steps()
        It is up to the subclass to set self._code
        """
        self._binary_data = base64.b64decode(self._code)  # Decode the encoded string into binary data
        self._offset = 0  # Reset the offset index of the binary data
        self._decode_steps()

    def _decode_steps(self) -> None:
        """
        This is meant to be overridden by the subclass.
        Keep these steps as simple as possible, 1 or 2 lines or break them out into another method.
        When the steps are complete all the binary data should be unpacked into `self.data`
        """
        pass

    def _encode(self) -> None:
        """
        Resets self._binary_data, runs self._encode_steps and encodes the new binary data to self._code
        It is up to the subclass to reveal self._code to the user or application.
        """
        self._binary_data = bytearray()
        self._encode_steps()
        self._code = base64.b64encode(self._binary_data)

    def _encode_steps(self) -> None:
        """
        This is meant to be overridden by the subclass.
        Keep these steps as simple as possible, 1 or 2 lines or break them out into another method.
        When the steps are complete everything in `self.data` should be packed into `self._binary_data`
        """
        pass

    def _unpack_u8(self) -> int:
        """Unpacks a u8 - Unsigned 8-bit integer (1 byte)"""
        result, = struct.unpack_from("<B", self._binary_data, self._offset)
        self._offset += 1
        return result

    def _unpack_u16(self) -> int:
        """Unpacks a u16 - Unsigned Short Integer (2 bytes)"""
        result, = struct.unpack_from("<H", self._binary_data, self._offset)
        self._offset += 2
        return result

    def _unpack_u32(self) -> int:
        """Unpacks a u32 - Unsigned 32-bit Integer (4 bytes)"""
        result, = struct.unpack_from("<I", self._binary_data, self._offset)
        self._offset += 4
        return result

    def _unpack_u64(self) -> int:
        """Unpacks a u64 - Unsigned 64-bit integer (8 bytes)"""
        result, = struct.unpack_from("<Q", self._binary_data, self._offset)
        self._offset += 8
        return result

    def _unpack_utf8(self, num_bytes: int) -> str:
        """
        Unpacks a UTF-8 string of fixed length.

        Args:
            num_bytes (int): Number of bytes to read from the stream.

        Returns:
            str: Decoded UTF-8 string
        """
        result, = struct.unpack_from(f"<{num_bytes}s", self._binary_data, self._offset)
        self._offset += num_bytes
        return result

    def _unpack_i32(self) -> int:
        """Unpacks an i32 - Signed 32-bit integer (4 bytes)"""
        result, = struct.unpack_from("<i", self._binary_data, self._offset)
        self._offset += 4
        return result

    def _unpack_uuid(self) -> str:
        """Unpacks a UUID - 128-bit identifier (16 bytes)"""
        result, = struct.unpack_from(f"16s", self._binary_data, self._offset)
        self._offset += 16
        return str(uuid.UUID(bytes=result))

    def _unpack_slab_uuid(self) -> str:
        """Unpacks a slab UUID - 128-bit identifier (16 bytes, mixed-endian layout)"""
        fields = struct.unpack_from("<IHH8B", self._binary_data, self._offset)
        self._offset += 16
        asset_uuid = uuid.UUID(
            fields=(
                fields[0],
                fields[1],
                fields[2],
                fields[3],
                fields[4],
                int.from_bytes(fields[5:], byteorder="big")
            )
        )
        return str(asset_uuid)

    def _pack_u8(self, value: int) -> None:
        """
        Packs a u8 - Unsigned 8-bit integer (1 byte)

        Args:
            value: The integer value to pack.
        """
        self._binary_data.extend(struct.pack("<B", value))

    def _pack_u16(self, value: int) -> None:
        """
        Packs a u16 - Unsigned 16-bit integer (2 bytes)

        Args:
            value: The integer value to pack.
        """
        self._binary_data.extend(struct.pack("<H", value))

    def _pack_u32(self, value: int) -> None:
        """
        Packs a u32 - Unsigned 32-bit integer (4 bytes)

        Args:
            value: The integer value to pack.
        """
        self._binary_data.extend(struct.pack("<I", value))

    def _pack_u64(self, value: int) -> None:
        """
        Packs a u64 - Unsigned 64-bit Integer (8 bytes)

        Args:
            value: The integer value to pack.
        """
        self._binary_data.extend(struct.pack("<Q", value))

    def _pack_uuid(self, uuid_str: str) -> None:
        """
        Packs a UUID - 128-bit identifier (16 bytes)

        Args:
            uuid_str: The UUID string.
        """
        self._binary_data.extend(uuid.UUID(uuid_str).bytes)

    def _pack_slab_uuid(self, uuid_str: str):
        """
        Packs a Slab UUID - 128-bit identifier (16 bytes, mixed-endian layout)

        Args:
            uuid_str: The UUID String.
        """
        fields = uuid.UUID(uuid_str).fields

        node_bytes = fields[5].to_bytes(6, byteorder="big")

        self._binary_data.extend(struct.pack(
            "<IHH8B",
            fields[0], fields[1], fields[2], fields[3], fields[4], *node_bytes
        ))

    def _pack_i32(self, value: int):
        """
        Packs an i32 - Signed 32-bit integer (4 bytes)

        Args:
            value: The integer to pack.
        """
        self._binary_data.extend(struct.pack("<i", value))
