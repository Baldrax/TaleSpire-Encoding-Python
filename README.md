# TaleSpire-Encoding-Python
Encoding/Decoding tools for TaleSpire

This repository is just getting started.

It currently contains two encoding types:
- Slabs (v1, v2)
- Creature Blueprints (v1, v2)

Slabs Example usage:
```python
from ts_encoding.slab import TSSlab

example_slab_code = ("H4sIAAAAAAAACjv369xFJgZGBgYGgUWHGX9Pme/S4z7T7pZ"
                     "doRonUGwCSIKhgRFMS0L4DTwMDCcYwOIsDBDADOZLQsRB8g"
                     "xQPgOcDwD7jJ0vaAAAAA==")

slab = TSSlab()
slab.decode_slab(example_slab_code)

# The slab contents are now in a dictionary `slab.data`
from pprint import pprint
pprint(slab.data)

"""
{'layout_count': 1,
 'layouts': [{'instance_count': 9,
              'instances': [{'degrees': 90.0,
                             'pos_x': 0.0,
                             'pos_y': 0.0,
                             'pos_z': 4.0},
                            {'degrees': 0.0,
                             'pos_x': 4.0,
                             'pos_y': 0.0,
                             'pos_z': 4.0},
                            {'degrees': 0.0,
                             'pos_x': 2.0,
                             'pos_y': 0.0,
                             'pos_z': 4.0},
                            {'degrees': 270.0,
                             'pos_x': 0.0,
                             'pos_y': 0.0,
                             'pos_z': 2.0},
                            {'degrees': 180.0,
                             'pos_x': 0.0,
                             'pos_y': 0.0,
                             'pos_z': 0.0},
                            {'degrees': 0.0,
                             'pos_x': 4.0,
                             'pos_y': 0.0,
                             'pos_z': 2.0},
                            {'degrees': 0.0,
                             'pos_x': 2.0,
                             'pos_y': 0.0,
                             'pos_z': 2.0},
                            {'degrees': 0.0,
                             'pos_x': 4.0,
                             'pos_y': 0.0,
                             'pos_z': 0.0},
                            {'degrees': 0.0,
                             'pos_x': 2.0,
                             'pos_y': 0.0,
                             'pos_z': 0.0}],
              'reserved': 0,
              'uuid': '01c3a210-94fb-449f-8c47-993eda3e7126'}],
 'magic_num': 3520002766,
 'num_creatures': 0,
 'version': 2}
"""

# To encode the data
new_slab_code = slab.encode_slab()
# The new_slab_code can be pasted into TaleSpire

# To create the data start a new TSSlab and edit the data dictionary.
# Each uuid is a new layout in the dictionary it is currently up to you
#  to format the dictionary properly so that it encodes correctly.
# In future versions there may be tools to help build the layouts.

# Here is an example of creating a single grass tile
new_slab = TSSlab()
new_slab.data["layout_count"] = 1
grass_layout = {
    "instance_count": 1, # The number of grass tiles
    "instances": [{
        "degrees": 0.0, # Yaw rotation in degrees 0-360 it is up to you to give valid values
        "pos_x": 0.0, # X position within slab
        "pos_y": 0.0, # Y position within slab
        "pos_z": 0.0}], # Z position within slab
    "reserved": 0, # Always set to 0
    "uuid": "01c3a210-94fb-449f-8c47-993eda3e7126" # Asset UUID
}
new_slab.data["layouts"].append(grass_layout)
new_slab_code = new_slab.encode_slab()

# You can paste that new_slab_code into TaleSpire to see your grass tile
```

Creature Blueprint Example usage:
```python
from ts_encoding.creature_bp import TSCreature
from pprint import pprint

url_from_TS = ("talespire://creature-blueprint/"
              "AgAMV2hpdGUgTWVlcGxlAQAAACMAYnI6MDAwMDAwMDAwMDAwMDAwMD"
              "AwMDAwMDAwMDQ3MDQxMDABAAAAAI49u_vNJQRDrZctETEJKR8ABAAA"
              "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAgQQAAIEEAACBBAAAgQQ"
              "AAIEEAACBBAAAgQQAAIEEAACBBAAAgQQAAIEEAACBBAAAgQQAAIEEA"
              "ACBBAAAgQQAAIEEAACBBAAAA")

bp = TSCreature()
bp.decode_url(url_from_TS)
pprint(bp.data)

# You can change any of the data in `bp.data`
bp.data["name"] = "New Name"
bp.data["stats"][0] = {"max": 100.0, "value": 100.0}  # Changes hp to 100

# To re-encode the data
new_url = bp.encode_url()

print(new_url)  # You can copy/paste this new URL into TaleSpire
```
