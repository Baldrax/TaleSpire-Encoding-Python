"""
Encoding Schemes for TaleSpire Slabs
v2 of this format is documented here:
https://github.com/Bouncyrock/DumbSlabStats/blob/master/format.md

v1 of the format was pieced together from various other projects.
"""
from __future__ import annotations

import gzip
import struct

from ts_encoding.common import TSCodingBase
from ts_encoding import SlabExceedsSizeLimit, BadSlabCode, UnsupportedSlabVersion

DEFAULT_SLAB_VERSION = 2 # This is the default version of new slabs being created.
SLAB_VERSIONS = [1,2] # List of supported versions
SLAB_MAGIC_NUM = 3520002766
SLAB_SIZE_LIMIT = 30720 # The limit in kB that a slab can be encoded as.


class TSSlab(TSCodingBase):
    """
    A Class to Decode and Encode a TaleSpire Slab.
    """

    def __init__(self):
        super().__init__()
        self._layout_count = 0
        self._force_version = None

    def _init_data(self) -> None:
        """Initializes the slab data to a default state."""
        self.data = {
            "magic_num": SLAB_MAGIC_NUM,
            "version": DEFAULT_SLAB_VERSION,
            "layout_count": 0,
            "num_creatures": 0,
            "layouts": [],
        }

    def decode_slab(self, slab_str) -> None:
        """
        Decode the given slab string.

        Args:
            slab_str: The slab string as copied from TaleSpire
        """
        self._code = slab_str.encode("ascii")
        self._decode()

    def _decode_steps(self) -> None:
        """
        The steps to decode the data.
        Each step is broken down to a few lines or method for ease of debugging and updating the schema.
        After this is run the entire slab should be decoded and stored in `self.data`.
        """
        self._decompress_data()
        self._decode_magic_number()
        self._decode_version()

        self.data["layout_count"] = self._layout_count = self._unpack_u16()

        if self._version > 1:
            self.data["num_creatures"] = self._unpack_u16()  # Number of Creatures is in v2 and higher.

        self._decode_layouts()

        if self._version == 1:
            self._decode_instances_v1()
        else:
            self._decode_instances_v2()

    def _decompress_data(self) -> None:
        """Unzip the Data."""
        try:
            self._binary_data = gzip.decompress(self._binary_data)
        except gzip.BadGzipFile:
            raise BadSlabCode("Failed to decompress the slab code, corrupt code or not a TS Slab Code.")

    def _decode_magic_number(self) -> None:
        """Unpack and verify the magic number."""
        self.data["magic_num"] = self._unpack_u32()

        if self.data["magic_num"] != SLAB_MAGIC_NUM:
            raise BadSlabCode(f"Not a TaleSpire Slab!\n"
                              f"\tGot Magic Number: {self.data['magic_num']}\n"
                              f"\tInstead of: {SLAB_MAGIC_NUM}")

    def _decode_version(self) -> None:
        """Unpack and verify the slab version."""
        self._version = self._unpack_u16()  # Unpack the version of the slab so we know which schema to use.
        self.data["version"] = self._version
        if self._version not in SLAB_VERSIONS:
            raise UnsupportedSlabVersion(f"Version ({self._version}) is not supported, "
                                         f"valid slab versions are [{', '.join(str(x) for x in SLAB_VERSIONS)}]")

    def _decode_layouts(self) -> None:
        """Unpack all of the UUID layouts."""
        for n in range(self._layout_count):
            uuid = self._unpack_slab_uuid()
            asset_count = self._unpack_u16()
            reserved = self._unpack_u16()
            self.data["layouts"].append(
                {
                    "uuid": uuid,
                    "instance_count": asset_count,
                    "reserved": reserved,
                    "instances": []
                }
            )

    def _decode_instances_v1(self) -> None:
        """Decode the v1 slab format Instances."""
        for asset in self.data["layouts"]:
            for n in range(asset["instance_count"]):
                pos = struct.unpack_from("<3f", self._binary_data, self._offset)  # 3 floats
                self._offset += 12

                size = struct.unpack_from("<3f", self._binary_data, self._offset)  # 3 floats
                self._offset += 12

                rot = self._unpack_u8()

                self._offset += 3  # For ignored data

                instance_data = {
                    "pos_x": pos[0],
                    "pos_y": pos[1],
                    "pos_z": pos[2],
                    "size_x": size[0],
                    "size_y": size[1],
                    "size_z": size[2],
                    "degrees": rot * 22.5
                }
                asset["instances"].append(instance_data)

    def _decode_instances_v2(self) -> None:
        """Decode the v2 slab format instances."""
        for asset in self.data["layouts"]:
            for n in range(asset["instance_count"]):
                packed_transform = self._unpack_u64()
                unused = (packed_transform >> 59) & 0b11111
                rot = (packed_transform >> 54) & 0b11111
                pos_x = (packed_transform >> 36) & 0x3FFFF
                pos_y = (packed_transform >> 18) & 0x3FFFF
                pos_z = packed_transform & 0x3FFFF
                instance_data = {
                    "degrees": rot * 15.0,
                    "pos_x": pos_x / 100.0,
                    "pos_y": pos_y / 100.0,
                    "pos_z": pos_z / 100.0
                }
                asset["instances"].append(instance_data)

    def encode_slab(self, force_version: int | None = None, ignore_limit: bool = False) -> str:
        """
        Triggers the encoding process and returns the results as an ascii string.

        Args:
            force_version: Forces encoding to a specific version schema (1,2)
            ignore_limit: Set to True to ignore the 30kB TaleSpire limit.

        Returns:
            str: The encoded slab string ready to paste into TaleSpire
        """
        if force_version:
            self._force_version = force_version
        self._encode()
        if len(self._binary_data) > SLAB_SIZE_LIMIT and not ignore_limit:
            raise SlabExceedsSizeLimit("Slab exceeds TaleSpire size limit of 30kB (30720 bytes) binary data!")
        return self._code.decode("ascii")

    def _encode_steps(self) -> None:
        """
        The steps to encode the data.
        Each step is broken down to a single line or method for ease of debugging and updating the schema.
        After this is run the entire slab should be encoded and stored in `self.binary_data`.
        """
        self._pack_u32(self.data["magic_num"])
        if self._force_version:
            self._version = self._force_version
        else:
            self._version = self.data["version"]

        self._pack_u16(self._version)
        self._pack_u16(self.data["layout_count"])

        if self._version > 1:
            self._pack_u16(self.data["num_creatures"])

        self._encode_layouts()

        if self._version == 1:
            self._encode_instances_v1()
        else:
            self._encode_instances_v2()

        self._binary_data = gzip.compress(self._binary_data, compresslevel=9)

    def _encode_layouts(self) -> None:
        """Encode the UUID Layouts."""
        for layout in self.data["layouts"]:
            uuid_str = layout["uuid"]
            if "reserved" in layout.keys():
                reserved = layout["reserved"]
            else:
                reserved = 0
            instance_count = len(layout["instances"])
            self._pack_slab_uuid(uuid_str)
            self._pack_u16(instance_count)
            self._pack_u16(reserved)

    def _encode_instances_v1(self) -> None:
        """Encode the v1 slab format instances."""
        for asset in self.data["layouts"]:
            for data in asset["instances"]:
                pos = (data["pos_x"], data["pos_y"], data["pos_z"])
                size = (data["size_x"], data["size_y"], data["size_z"])
                rot = int(data["degrees"]/22.5)

                self._binary_data.extend(struct.pack("<3f", *pos))
                self._binary_data.extend(struct.pack("<3f", *size))
                self._pack_u8(rot)
                self._binary_data.extend(struct.pack("3x"))  # 3 bytes of empty data

    def _encode_instances_v2(self) -> None:
        """Encode the v2 slab format instances."""
        offset_x = offset_y = offset_z = 0
        if self.data["version"] == 1:
            # Attempt to convert v1 slabs to v2 slabs
            # This may not work
            min_x = min_y = min_z = 0
            for asset in self.data["layouts"]:
                for data in asset["instances"]:
                    min_x = min(min_x, data["pos_x"])
                    min_y = min(min_y, data["pos_y"])
                    min_z = min(min_z, data["pos_z"])
            offset_x = abs(min_x)
            offset_y = abs(min_y)
            offset_z = abs(min_z)

        for asset in self.data["layouts"]:
            for data in asset["instances"]:
                unused = 0
                rot = int(data["degrees"] / 15) & 0b11111
                pos_x = int((data["pos_x"] + offset_x) * 100) & 0x3FFFF
                pos_y = int((data["pos_y"] + offset_y) * 100) & 0x3FFFF
                pos_z = int((data["pos_z"] + offset_z) * 100) & 0x3FFFF

                packed = (
                    (unused << 59) |
                    (rot << 54) |
                    (pos_x << 36) |
                    (pos_y << 18) |
                    pos_z
                )
                self._pack_u64(packed)
