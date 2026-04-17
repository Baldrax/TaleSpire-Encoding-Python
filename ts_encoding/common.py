# Encoding Schemes for TS:
# https://talespire.com/url-scheme
#
# Byte order is little-endian
import base64
import struct
import uuid


class TSCodingBase:
    """
    A Base Class to Decode and Encode a TaleSpire content.
    """

    def __init__(self):
        self.data = {}
        self._init_data()
        self._version = 0
        self._encode_version = 2
        self._code = None
        self._binary_data = None
        self._offset = 0

    def _init_data(self):
        self.data = {
            "version": 1,
        }

    def _decode(self) -> None:
        """
        The steps to decode the data.
        Each step is broken down to a single line or method for ease of debugging and updating the schema.
        After this is run the entire blueprint should be decoded and stored in `self.data`.
        """
        self._binary_data = base64.b64decode(self._code)  # Decode the encoded string into binary data
        self._offset = 0  # Reset the offset index of the binary data
        self._decode_steps()

    def _decode_steps(self):
        pass

    def _encode(self) -> None:
        """
        The steps to encode the data.
        Each step is broken down to a single line or method for ease of debugging and updating the schema.
        After this is run the entire blueprint should be encoded and stored in `self.binary_data`.
        """
        self._binary_data = bytearray()
        self._encode_steps()
        self._code = base64.b64encode(self._binary_data)

    def _encode_steps(self):
        pass

    def _unpack_u8(self) -> int:
        """
        Unpacks a u8 - Unsigned Char Integer

        Returns:
            int:
        """
        result, = struct.unpack_from("<B", self._binary_data, self._offset)
        self._offset += 1
        return result

    def _unpack_u16(self) -> int:
        """
        Unpacks a u16 - Unsigned Short Integer

        Returns:
            int:
        """
        # The class stores the binary data and an offset which represents the current position/index
        #  we are at in the binary data.
        # Each unpack method then increments the offset by the proper amount so we can decode the next
        #  step without having to feed in the offset index.
        result, = struct.unpack_from("<H", self._binary_data, self._offset)
        self._offset += 2
        return result

    def _unpack_u32(self) -> int:
        """
        Unpacks a u32 - Unsigned Long Integer

        Returns:
            int:
        """
        result, = struct.unpack_from("<I", self._binary_data, self._offset)
        self._offset += 4
        return result

    def _unpack_u64(self) -> int:
        result, = struct.unpack_from("<Q", self._binary_data, self._offset)
        self._offset += 8
        return result

    def _unpack_utf8(self, num_chars: int) -> str:
        """
        Unpacks a utf8 string of characters from the binary data.
        The number of characters must be provided.

        Args:
            num_chars: The number of characters to unpack.

        Returns:
            str: The extracted string.
        """
        result, = struct.unpack_from(f"<{num_chars}s", self._binary_data, self._offset)
        self._offset += num_chars
        return result

    def _unpack_i32(self) -> int:
        """
        Unpacks an i32 - 32-bit signed integer

        Returns:
            int:
        """
        result, = struct.unpack_from("<i", self._binary_data, self._offset)
        self._offset += 4
        return result

    def _unpack_uuid(self) -> str:
        """Unpacks the UUID string.

        Returns:
            str:
        """
        result, = struct.unpack_from(f"<16s", self._binary_data, self._offset)
        self._offset += 16
        return str(uuid.UUID(bytes=result))

    def _unpack_slab_uuid(self) -> str:
        """Unpacks the UUID from a Slab

        Returns:
            str:
        """
        uuid_data = struct.unpack_from("<IHH8B", self._binary_data, self._offset)
        self._offset += 16
        asset_uuid = uuid.UUID(
            fields=(
                uuid_data[0], uuid_data[1], uuid_data[2], uuid_data[3], uuid_data[4],
                int.from_bytes(uuid_data[5:], byteorder="big")
            )
        )
        return str(asset_uuid)

    def _pack_u8(self, value: int):
        """
        Packs a u8 - Unsigned Char Integer

        Args:
            value: The integer value to pack.
        """
        self._binary_data.extend(struct.pack("<B", value))

    def _pack_u16(self, value: int):
        """
        Packs a u16 - Unsigned Short Integer
        Args:
            value: The integer value to pack.
        """
        self._binary_data.extend(struct.pack("<H", value))

    def _pack_u32(self, value: int):
        """
        Packs a u32 - Unsigned Long Integer
        Args:
            value: The integer value to pack.
        """
        self._binary_data.extend(struct.pack("<I", value))

    def _pack_u64(self, value: int):
        """
        Packs a u64 - Unsigned Long Integer
        Args:
            value: The integer value to pack.
        """
        self._binary_data.extend(struct.pack("<Q", value))

    def _pack_uuid(self, uuid_str: str):
        """
        Packs a UUID.
        Args:
            uuid_str: The UUID string.
        """
        self._binary_data.extend(uuid.UUID(uuid_str).bytes)

    def _pack_slab_uuid(self, uuid_str: str):
        """Packs a Slab UUID
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
        Packs an i32 - 32-bit integer.
        Args:
            value: The integer to pack.
        """
        self._binary_data.extend(struct.pack("<i", value))
