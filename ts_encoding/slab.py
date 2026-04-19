# Encoding Schemes for TS:
# https://talespire.com/url-scheme
from __future__ import annotations

import gzip
import struct

from ts_encoding.common import TSCodingBase


class TSSlab(TSCodingBase):
    """
    A Class to Decode and Encode a TaleSpire Slab.
    """

    def __init__(self):
        super().__init__()
        self._layout_count = 0
        self._force_version = None

    def _init_data(self):
        self.data = {
            "magic_num": 3520002766,
            "version": 2,
            "layout_count": 0,
            "num_creatures": 0,
            "layouts": [],
        }

    def decode_slab(self, slab_str):
        self._code = slab_str.encode("ascii")
        self._decode()

    def _decode_steps(self):
        self._binary_data = gzip.decompress(self._binary_data) # Unzip the data
        self.data["magic_num"] = self._unpack_u32()
        self._version = self._unpack_u16()  # Unpack the version of the slab so we know which schema to use.
        self.data["version"] = self._version
        self._layout_count = self._unpack_u16()
        self.data["layout_count"] = self._layout_count

        if self._version > 1:
            self.data["num_creatures"] = self._unpack_u16()  # Number of Creatures is in v2 and higher.
        self._decode_layouts()

        if self._version == 1:
            self._decode_instances_v1()
        else:
            self._decode_instances_v2()

    def _decode_layouts(self):
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

    def _decode_instances_v1(self):
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

    def _decode_instances_v2(self):
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

    def encode_slab(self, force_version: int | None = None):
        if force_version:
            self._force_version = force_version
        self._encode()
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

    def _encode_layouts(self):
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

    def _encode_instances_v1(self):
        for asset in self.data["layouts"]:
            for data in asset["instances"]:
                pos = (data["pos_x"], data["pos_y"], data["pos_z"])
                size = (data["size_x"], data["size_y"], data["size_z"])
                rot = int(data["degrees"]/22.5)

                self._binary_data.extend(struct.pack("<3f", *pos))
                self._binary_data.extend(struct.pack("<3f", *size))
                self._pack_u8(rot)
                self._binary_data.extend(struct.pack("3x"))  # 3 bytes of empty data

    def _encode_instances_v2(self):

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
