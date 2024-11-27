# Encoding Schemes for TS:
# https://talespire.featureos.help/en/articles/talespire-url-scheme

import base64
import struct
import uuid

from pprint import pprint


class TSCreature:

    def __init__(self):
        self.data = {
            "version": 1,
            "name": "",
            "morph_ids": [],
            "active_morph_index": 0,
            "morph_scales": [1.0] * 10,
            "reserved0": [0] * 8,
            "reserved1": [0] * 3,
            "stats": [{"max": 0, "value": 0}] * 9,
            "torch_enabled": False,
            "explicitly_hidden": False,
            "flying_enabled": False,
            "slot_overrides": [],
            "active_emote_ids": [],
        }
        self.code = None
        self.binary_data = None
        self.offset = 0

    def decode_url(self, url):
        self.code = url.split("/")[-1].replace("_", "/")
        self.decode()

    def decode(self):
        self.binary_data = base64.b64decode(self.code)
        self.offset = 0

        version = self.unpack_u16()
        self.data["version"] = version
        self.decode_name()
        self.decode_morph_ids()
        self.data["active_morph_index"] = self.unpack_u8()
        self.decode_morph_scales()
        self.decode_reserved()
        self.decode_stats()
        self.decode_torch_hide_fly()
        self.decode_slot_overrides()
        self.decode_active_emote_ids()

    def decode_name(self):
        num_chars = self.unpack_u8()
        if num_chars > 150:
            raise ValueError("number-of-stats exceeds 150")
        self.data["name"] = self.unpack_utf8(num_chars).decode()

    def decode_morph_ids(self):
        num_morph_ids = self.unpack_u8()
        morph_ids = []
        for _ in range(num_morph_ids):
            morph_ids.append(self.unpack_uuid())
        self.data["morph_ids"] = morph_ids

    def decode_morph_scales(self):
        packed_morph_scales, = struct.unpack_from("<Q", self.binary_data, self.offset)
        self.offset += 8
        morph_scales = []
        for n in range(10):
            scale_bits = (packed_morph_scales >> (n * 6)) & 0b111111
            scale = scale_bits / 4
            morph_scales.append(scale)

        self.data["morph_scales"] = morph_scales

    def decode_reserved(self):
        reserved0 = struct.unpack_from("<8H", self.binary_data, self.offset)
        self.offset += 16
        self.data["reserved0"] = reserved0
        reserved1 = struct.unpack_from("<3B", self.binary_data, self.offset)
        self.offset += 3
        self.data["reserved1"] = reserved1

    def decode_stats(self):
        stats = []
        for _ in range(9):
            value, v_max = self.unpack_stat()
            stats.append({"value": value, "max": v_max})
        self.data["stats"] = stats

    def decode_torch_hide_fly(self):
        state = self.unpack_u8()
        self.data["torch_enabled"] = bool(state & 0b00000001)
        self.data["explicitly_hidden"] = bool(state & 0b00000010)
        self.data["flying_enabled"] = bool(state & 0b00000100)

    def decode_slot_overrides(self):
        num_overrides = self.unpack_u8()
        if num_overrides > 16:
            raise ValueError("number-of-emote-slot-overrides exceeds 16")

        slot_overrides = []
        for _ in range(num_overrides):
            slot_id = self.unpack_uuid()
            slot_index = self.unpack_u16()
            slot_overrides.append({"id": slot_id, "index": slot_index})
        self.data["slot_overrides"] = slot_overrides

    def decode_active_emote_ids(self):
        num_active_emotes = self.unpack_u8()
        active_emote_ids = []
        for _ in range(num_active_emotes):
            emote_id = self.unpack_uuid()
            active_emote_ids.append(emote_id)
        self.data["active_emote_ids"] = active_emote_ids

    def unpack_u16(self):
        result, = struct.unpack_from("<H", self.binary_data, self.offset)
        self.offset += 2
        return result

    def unpack_u8(self):
        result, = struct.unpack_from("<B", self.binary_data, self.offset)
        self.offset += 1
        return result

    def unpack_utf8(self, num_chars):
        result = self.binary_data[self.offset:self.offset+num_chars]
        self.offset += num_chars
        return result

    def unpack_uuid(self):
        result = self.binary_data[self.offset:self.offset + 16]
        self.offset += 16
        return str(uuid.UUID(bytes=result))

    def unpack_stat(self):
        value, v_max = struct.unpack_from("<ff", self.binary_data, self.offset)
        self.offset += 8
        return value, v_max

    def encode(self):
        self.binary_data = bytearray()

        version = self.data["version"]

        self.pack_u16(version)
        self.encode_name()
        self.encode_morph_ids()
        self.pack_u8(self.data["active_morph_index"])
        self.encode_morph_scales()
        self.encode_reserved()
        self.encode_stats()
        self.encode_torch_hide_fly()
        self.encode_slot_overrides()
        self.encode_active_emote_ids()

    def encode_url(self):
        self.encode()
        encoded_data = base64.b64encode(bytes(self.binary_data)).decode()
        encoded_data.replace("/", "_")
        url = f"talespire://creature-blueprint/{encoded_data}"
        return url

    def encode_name(self):
        name = self.data["name"].encode("utf-8")
        self.pack_u8(len(name))
        self.binary_data.extend(name)

    def encode_morph_ids(self):
        morph_ids = self.data["morph_ids"]
        self.pack_u8(len(morph_ids))
        for morph_id in morph_ids:
            self.pack_uuid(morph_id)

    def encode_morph_scales(self):
        packed_morph_scales = 0
        for i, scale in enumerate(self.data["morph_scales"]):
            scale_bits = int(scale * 4) & 0b111111
            packed_morph_scales |= (scale_bits << (i * 6))
        self.binary_data.extend(struct.pack("<Q", packed_morph_scales))

    def encode_reserved(self):
        reserved = self.data["reserved0"] + self.data["reserved1"]
        self.binary_data.extend(struct.pack("<8H3B", *reserved))

    def encode_stats(self):
        for stat in self.data["stats"]:
            self.pack_stat((stat["value"], stat["max"]))

    def encode_torch_hide_fly(self):
        state = (
                (1 if self.data["torch_enabled"] else 0) |
                (2 if self.data["explicitly_hidden"] else 0) |
                (4 if self.data["flying_enabled"] else 0)
        )
        self.pack_u8(state)

    def encode_slot_overrides(self):
        slot_overrides = self.data["slot_overrides"]
        self.pack_u8(len(slot_overrides))
        for slot in slot_overrides:
            self.pack_uuid(slot["id"])
            self.pack_u16(slot["index"])

    def encode_active_emote_ids(self):
        active_emote_ids = self.data["active_emote_ids"]
        self.pack_u8(len(active_emote_ids))
        for emote_id in active_emote_ids:
            self.pack_uuid(emote_id)

    def pack_u8(self, data):
        self.binary_data.extend(struct.pack("<B", data))

    def pack_u16(self, data):
        self.binary_data.extend(struct.pack("<H", data))

    def pack_uuid(self, uuid_str):
        self.binary_data.extend(uuid.UUID(uuid_str).bytes)

    def pack_stat(self, stat_tuple):
        value, v_max = stat_tuple
        self.binary_data.extend(struct.pack("<ff", value, v_max))


# sample_url = "talespire://creature-blueprint/AgD_AQAAACMAYnI6MDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwZjY2ZjQxMDABAAAAAIkMFyRfeChLqZlY6EwXNW0ABAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAgQQAAIEEAACBBAAAgQQAAIEEAACBBAAAgQQAAIEEAACBBAAAgQQAAIEEAACBBAAAgQQAAIEEAACBBAAAgQQAAIEEAACBBAAAA"
#sample_url = "talespire://creature-blueprint/AgD_AQAAACEAOmExMjcxNGQ3MzU1NWE3NGY4MmQ3NGNhMWU3NWVkYmZkAQAAAABh+rL0znE5RrynJkTEzlgPAAQAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAIEEAACBBAAAgQQAAIEEAACBBAAAgQQAAIEEAACBBAAAgQQAAIEEAACBBAAAgQQAAIEEAACBBAAAgQQAAIEEAACBBAAAgQQAAAA=="
sample_2 = "talespire://creature-blueprint/AgD_AQAAACEAOmExMjcxNGQ3MzU1NWE3NGY4MmQ3NGNhMWU3NWVkYmZkAQAAAABh+rL0znE5RrynJkTEzlgPAAQAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAIEEAACBBAAAgQQAAIEEAACBBAAAgQQAAIEEAACBBAAAgQQAAIEEAACBBAAAgQQAAIEEAACBBAAAgQQAAIEEAACBBAAAgQQQAAA=="
sample_url = "talespire://creature-blueprint/AQAHQWJvbGV0aAFKbKpDJxNtSIiDNlZLt1zmAAgAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAWEMAAFhDAACIQQAAiEEAACBBAAAgQgAAoEAAAKBAAACAvwAAgL8AAABAAAAAQAAAgEAAAIBAAAAAQAAAAEAAAIBAAACAQAAAAA=="
# sample_url = "talespire://creature-blueprint/AQAcQWR1bHQgR3JlZW4gRHJhZ29uPHNpemU9MD57fQHl+jncR3fYR4Xpu4q6uML0AAwAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAmUMAAJlDAACYQQAAmEEAACBCAACgQgAAwEAAAMBAAACAPwAAgD8AAKBAAACgQAAAgEAAAIBAAAAAQAAAAEAAAEBAAABAQAAAAA=="
creature = TSCreature()
creature.decode_url(sample_url)
# creature.data["name"] = "Bad Boy"
# creature.data["stats"][0] = {"max": 500, "value": 333}
# creature.data["torch_enabled"] = True
# creature.data["flying_enabled"] = True
pprint(creature.data)
# print(creature.encode_url())
