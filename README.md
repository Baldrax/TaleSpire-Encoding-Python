# TaleSpire-Encoding-Python
Encoding/Decoding tools for TaleSpire

This repository is just getting started.

It currently contains ts_encoding.creature_bp which has a class for
Encoding and Decoding TaleSpire Creature Blueprints, it supports v1
and v2 of the schema.

Example usage:
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
