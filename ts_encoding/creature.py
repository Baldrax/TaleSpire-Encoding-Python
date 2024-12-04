# Encoding Schemes for TS:
# https://talespire.com/url-scheme
#
# Byte order is little-endian

import base64
import struct
import uuid

from pprint import pprint


class TSCreature:
    """
    A Class to Decode and Encode a TaleSpire Creature Blueprint
    """

    def __init__(self):
        self.data = {
            "version": 1,
            "name": "",
            "content_packs": [],
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
        self._version = 0
        self._code = None
        self._binary_data = None
        self._offset = 0

    def decode_url(self, url: str) -> None:
        """
        Decode a Creature Blueprint URL into the `data` attribute.
        Args:
            url: The Creature Blueprint URL as copied from a TaleSpire Creature.
        """
        # Extract just the code from the URL, this is the last element after splitting via "/"
        # Then replace "_" with "/" after extracting the code.
        #  This was likely done so the URL could be formed properly, the encoded string may contain "/" characters
        #  which are swapped to "_" characters which must not be used by base64 encoding.
        #  So they need to be swapped back.
        self._code = url.split("/")[-1].replace("_", "/")  # The code is stored if needed later.
        self._decode()

    def _decode(self) -> None:
        """
        The steps to decode the data.
        Each step is broken down to a single line or method for ease of debugging and updating the schema.
        After this is run the entire blueprint should be decoded and stored in `self.data`.
        """
        self._binary_data = base64.b64decode(self._code)  # Decode the encoded string into binary data
        self._offset = 0  # Reset the offset index of the binary data

        self._version = self._unpack_u16()  # Unpack the version of the blueprint so we know which schema to use.
        self.data["version"] = self._version
        self._decode_name()
        self._decode_content_packs()
        self._decode_morph_ids()
        self.data["active_morph_index"] = self._unpack_u8()  # Unpack and store the active morph index.
        self._decode_morph_scales()
        self._decode_reserved()
        self._decode_stats()
        self._decode_torch_hide_fly()
        self._decode_slot_overrides()
        self._decode_active_emote_ids()

    def _decode_name(self) -> None:
        """
        Decodes the name of the creature if it has been set.
        """
        num_chars = self._unpack_u8()
        if num_chars == 255:  # if the value is 255 that means the name has not been manually set, skip decoding.
            return
        elif num_chars > 150:  # the name must be less than 150 characters.
            raise ValueError("number-of-stats exceeds 150")

        # Set the extracted name.
        self.data["name"] = self._unpack_utf8(num_chars).decode()

    def _decode_content_packs(self) -> None:
        """
        Decodes the Content Packs.
        """
        if self._version < 2:  # This is only implemented in v2+ of the schema.
            return

        num_content_packs = self._unpack_i32()  # Get the number of content packs present.

        content_pack_uris = []
        for _ in range(num_content_packs):
            byte_count = self._unpack_u16()
            uri = self._unpack_utf8(byte_count).decode()
            content_pack_uris.append(uri)

        # Set the extracted content_packs
        self.data["content_packs"] = content_pack_uris

    def _decode_morph_ids(self) -> None:
        """
        Decode the Morph IDs, there is always at least one of these, the active ID of the creature.
        """
        num_morph_ids = self._unpack_u8()  # Get the number of Morph IDs, there should be at least 1.
        content_pack_index = None
        morph_ids = []
        for _ in range(num_morph_ids):
            if self._version > 1:  # Content pack index os only in v2+ of the schema.
                content_pack_index = self._unpack_i32()  # Unpack this even though it isn't needed in our data.
            content_pack_uuid = self._unpack_uuid()
            morph_ids.append(content_pack_uuid)

        # Set the extracted morph_ids
        self.data["morph_ids"] = morph_ids

    def _decode_morph_scales(self) -> None:
        """
        Decode the Morph Scales, this is the scale of the creature for each morph depicted.
        """
        # Parse the packed-morph-scales (u64)
        packed_morph_scales, = struct.unpack_from("<Q", self._binary_data, self._offset)  # Little-endian u64
        self._offset += 8

        morph_scales = []
        for n in range(10):  # Up to 10 morphs
            # Extract the nth 6-bit segment
            scale_bits = (packed_morph_scales >> (n * 6)) & 0b111111  # Mask 6 bits
            # Scale the value
            scale = scale_bits / 4
            morph_scales.append(scale)

        # Set the extracted scales
        self.data["morph_scales"] = morph_scales

    def _decode_reserved(self) -> None:
        """
        Decodes the reserved values in the creature.
        No Idea what these are for.
        """
        reserved0 = struct.unpack_from("<8H", self._binary_data, self._offset)  # Unpack 8 u16 values
        self._offset += 16
        # Store the u16 values in "reserved0" of the data
        self.data["reserved0"] = reserved0

        reserved1 = struct.unpack_from("<3B", self._binary_data, self._offset)  # Unpack 3 u8 values
        self._offset += 3
        # Store the u16 values in "reserved0" of the data
        self.data["reserved1"] = reserved1

    def _decode_stats(self) -> None:
        """
        Decodes the stats of the creature.
        The first value is the "hp" of the creature.
        The 8 additional values are as depicted in the campaign.
        """
        stats = []
        for _ in range(9):  # HP plus 8 assignable stats.
            value, v_max = self._unpack_stat()
            stats.append({"value": value, "max": v_max})  # Each stat has a value and a max value.

        # Set the extracted stats
        self.data["stats"] = stats

    def _decode_torch_hide_fly(self) -> None:
        """
        Decode the bits for the torch, hide, and fly states.
        These are stored in a single byte (u8) where each bit represents a specific state.
        """
        state = self._unpack_u8()  # Extract the byte
        self.data["torch_enabled"] = bool(state & 0b00000001)  # Mask for bit 0
        self.data["explicitly_hidden"] = bool(state & 0b00000010)  # Mask for bit 1
        self.data["flying_enabled"] = bool(state & 0b00000100)  # Mask for bit 2
        # There are 5 more bits (3-7) that are not used.

    def _decode_slot_overrides(self) -> None:
        """
        Decode the Emote Slot Overrides.
        These appear to be unused? Perhaps a placeholder for custom emotes in the future?

        So far I've not encountered a blueprint that contains these. - Baldrax
        """
        num_overrides = self._unpack_u8()
        if num_overrides > 16:  # These are limited to 16
            raise ValueError("number-of-emote-slot-overrides exceeds 16")

        slot_overrides = []
        for _ in range(num_overrides):
            slot_id = self._unpack_uuid()  # UUID of the slot
            slot_index = self._unpack_u16()  # Index of the slot
            # Until we figure out what these do they are just being stored in a dictionary
            slot_overrides.append({"id": slot_id, "index": slot_index})

        # Set the extracted slot overrides.
        self.data["slot_overrides"] = slot_overrides

    def _decode_active_emote_ids(self) -> None:
        """
        Decode the active emote ids.
        These store the persistent state of certain emotes, so far this just appears to be the "knockdown"/prone emote.
        """
        num_active_emotes = self._unpack_u8()  # The number of active emotes.
        active_emote_ids = []
        for _ in range(num_active_emotes):
            emote_id = self._unpack_uuid()  # The emote is identified by a UUID
            active_emote_ids.append(emote_id)

        # Set the active emote ids
        self.data["active_emote_ids"] = active_emote_ids

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

    def _unpack_u8(self) -> int:
        """
        Unpacks a u8 - Unsigned Char Integer

        Returns:
            int:
        """
        result, = struct.unpack_from("<B", self._binary_data, self._offset)
        self._offset += 1
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
        """
        Unpacks the uuid string.

        Returns:
            str:
        """
        result, = struct.unpack_from(f"<16s", self._binary_data, self._offset)
        self._offset += 16
        return str(uuid.UUID(bytes=result))

    def _unpack_stat(self) -> (float, float):
        """
        Unpacks a stat, this is stored as two 32-bit floats.

        Returns:
            tuple: A tuple containing two floats ( Value, Max Value )
        """
        value, v_max = struct.unpack_from("<ff", self._binary_data, self._offset)
        self._offset += 8
        return value, v_max

    def _encode(self) -> None:
        """
        The steps to encode the data.
        Each step is broken down to a single line or method for ease of debugging and updating the schema.
        After this is run the entire blueprint should be encoded and stored in `self.binary_data`.
        """
        self._binary_data = bytearray()

        version = self.data["version"]

        self._pack_u16(version)
        self._encode_name()
        self._encode_morph_ids()
        self._pack_u8(self.data["active_morph_index"])
        self._encode_morph_scales()
        self._encode_reserved()
        self._encode_stats()
        self._encode_torch_hide_fly()
        self._encode_slot_overrides()
        self._encode_active_emote_ids()

    def encode_url(self):
        self._encode()
        encoded_data = base64.b64encode(bytes(self._binary_data)).decode().replace("/", "_")
        url = f"talespire://creature-blueprint/{encoded_data}"
        return url

    def _encode_name(self):
        name = self.data["name"].encode("utf-8")
        self._pack_u8(len(name))
        self._binary_data.extend(name)

    def _encode_morph_ids(self):
        morph_ids = self.data["morph_ids"]
        self._pack_u8(len(morph_ids))
        for morph_id in morph_ids:
            self._pack_uuid(morph_id)

    def _encode_morph_scales(self):
        packed_morph_scales = 0
        for i, scale in enumerate(self.data["morph_scales"]):
            scale_bits = int(scale * 4) & 0b111111
            packed_morph_scales |= (scale_bits << (i * 6))
        self._binary_data.extend(struct.pack("<Q", packed_morph_scales))

    def _encode_reserved(self):
        reserved = self.data["reserved0"] + self.data["reserved1"]
        self._binary_data.extend(struct.pack("<8H3B", *reserved))

    def _encode_stats(self):
        for stat in self.data["stats"]:
            self._pack_stat((stat["value"], stat["max"]))

    def _encode_torch_hide_fly(self):
        state = (
                (1 if self.data["torch_enabled"] else 0) |
                (2 if self.data["explicitly_hidden"] else 0) |
                (4 if self.data["flying_enabled"] else 0)
        )
        self._pack_u8(state)

    def _encode_slot_overrides(self):
        slot_overrides = self.data["slot_overrides"]
        self._pack_u8(len(slot_overrides))
        for slot in slot_overrides:
            self._pack_uuid(slot["id"])
            self._pack_u16(slot["index"])

    def _encode_active_emote_ids(self):
        active_emote_ids = self.data["active_emote_ids"]
        self._pack_u8(len(active_emote_ids))
        for emote_id in active_emote_ids:
            self._pack_uuid(emote_id)

    def _pack_u8(self, data):
        self._binary_data.extend(struct.pack("<B", data))

    def _pack_u16(self, data):
        self._binary_data.extend(struct.pack("<H", data))

    def _pack_uuid(self, uuid_str):
        self._binary_data.extend(uuid.UUID(uuid_str).bytes)

    def _pack_stat(self, stat_tuple):
        value, v_max = stat_tuple
        self._binary_data.extend(struct.pack("<ff", value, v_max))


# sample_url = "talespire://creature-blueprint/AgD_AQAAACMAYnI6MDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwZjY2ZjQxMDABAAAAAIkMFyRfeChLqZlY6EwXNW0ABAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAgQQAAIEEAACBBAAAgQQAAIEEAACBBAAAgQQAAIEEAACBBAAAgQQAAIEEAACBBAAAgQQAAIEEAACBBAAAgQQAAIEEAACBBAAAA"
# sample_url = "talespire://creature-blueprint/AgD_AQAAACEAOmExMjcxNGQ3MzU1NWE3NGY4MmQ3NGNhMWU3NWVkYmZkAQAAAABh+rL0znE5RrynJkTEzlgPAAQAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAIEEAACBBAAAgQQAAIEEAACBBAAAgQQAAIEEAACBBAAAgQQAAIEEAACBBAAAgQQAAIEEAACBBAAAgQQAAIEEAACBBAAAgQQAAAA=="
# sample_2 = "talespire://creature-blueprint/AgD_AQAAACEAOmExMjcxNGQ3MzU1NWE3NGY4MmQ3NGNhMWU3NWVkYmZkAQAAAABh+rL0znE5RrynJkTEzlgPAAQAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAIEEAACBBAAAgQQAAIEEAACBBAAAgQQAAIEEAACBBAAAgQQAAIEEAACBBAAAgQQAAIEEAACBBAAAgQQAAIEEAACBBAAAgQQQAAA=="
# sample_url = "talespire://creature-blueprint/AQAHQWJvbGV0aAFKbKpDJxNtSIiDNlZLt1zmAAgAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAWEMAAFhDAACIQQAAiEEAACBBAAAgQgAAoEAAAKBAAACAvwAAgL8AAABAAAAAQAAAgEAAAIBAAAAAQAAAAEAAAIBAAACAQAAAAA=="
# sample_url = "talespire://creature-blueprint/AQAcQWR1bHQgR3JlZW4gRHJhZ29uPHNpemU9MD57fQHl+jncR3fYR4Xpu4q6uML0AAwAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAmUMAAJlDAACYQQAAmEEAACBCAACgQgAAwEAAAMBAAACAPwAAgD8AAKBAAACgQAAAgEAAAIBAAAAAQAAAAEAAAEBAAABAQAAAAA=="
# sample_url = "talespire://creature-blueprint/AgAJTXkgTWVlcGxlAQAAACMAYnI6MDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwZjY2ZjQxMDABAAAAAIkMFyRfeChLqZlY6EwXNW0ABAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAgQQAAIEEAACBBAAAgQQAAIEEAACBBAAAgQQAAIEEAACBBAAAgQQAAIEEAACBBAAAgQQAAIEEAACBBAAAgQQAAIEEAACBBAAAA"
# sample_url = "talespire://creature-blueprint/AgAJTXkgTWVlcGxlAQAAACMAYnI6MDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwZjY2ZjQxMDABAAAAAIkMFyRfeChLqZlY6EwXNW0ABAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAACAPwAAgD8AAABAAAAAQAAAQEAAAEBAAACAQAAAoEAAAKBAAACgQAAAwEAAAMBAAADgQAAA4EAAAABBAAAAQQAAEEEAABBBBQAA"
# sample_url = "talespire://creature-blueprint/AgD_AQAAACMAYnI6MDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwZjY2ZjQxMDABAAAAAIkMFyRfeChLqZlY6EwXNW0ABAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAgQQAAIEEAACBBAAAgQQAAIEEAACBBAAAgQQAAIEEAACBBAAAgQQAAIEEAACBBAAAgQQAAIEEAACBBAAAgQQAAIEEAACBBAAAA"
sample_url = "talespire://creature-blueprint/AgAMTWluZCBDcmF3bGVyAQAAACEAOmExMjcxNGQ3MzU1NWE3NGY4MmQ3NGNhMWU3NWVkYmZkAgAAAABFXKkyUnT7QYizDrku384MAAAAAJpAFVr7QUxOuKxXgt_rjtEABAIAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAgQQAAIEEAACBBAAAgQQAAIEEAACBBAAAgQQAAIEEAACBBAAAgQQAAIEEAACBBAAAgQQAAIEEAACBBAAAgQQAAIEEAACBBAAABpiVmgAKP_ku6ME6+lVNsBQ=="
creature = TSCreature()
creature.decode_url(sample_url)
# creature.data["name"] = "Bad Boy"
# creature.data["stats"][0] = {"max": 500, "value": 333}
# creature.data["torch_enabled"] = True
# creature.data["flying_enabled"] = True
pprint(creature.data)
# print(creature.encode_url())
