import pytest
from ts_encoding.creature_bp import TSCreature

# Blueprint v1 samples are from the 5e Database
#  https://talestavern.com/talespire-5e-creature-blueprint-database-2/

TEST_CASES = [
    pytest.param(
        {
            "url": "talespire://creature-blueprint"
                   "/AQAHQWJvbGV0aAFKbKpDJxNtSIiDNlZLt1zmAAgAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAWEMAAFhDAACIQQAA"
                   "iEEAACBBAAAgQgAAoEAAAKBAAACAvwAAgL8AAABAAAAAQAAAgEAAAIBAAAAAQAAAAEAAAIBAAACAQAAAAA==",
            "assert": {
                "name": "Aboleth",
                "flying_enabled": False,
                "morph_ids": [(None, "4a6caa43-2713-6d48-8883-36564bb75ce6")],
                "stats": {0: (216.0, 216.0), 8: (4.0, 4.0)}
            }
        },
        id="Aboleth from the 5e Database - bp(v1)"
    ),
    pytest.param(
        {
            "url": "talespire://creature-blueprint"
                   "/AQALV2F0ZXIgV2VpcmQBiP+KHsGG30W_tm3GProItwAIAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAMZCAADGQ"
                   "gAAUEEAAFBBAAAAAAAAcEIAAEBAAABAQAAAQEAAAEBAAACAPwAAgD8AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA=",
            "assert": {
                "name": "Water Weird",
                "flying_enabled": False,
                "morph_ids": [(None, "88ff8a1e-c186-df45-bfb6-6dc63eba08b7")],
                "stats": {0: (99.0, 99.0), 8: (0.0, 0.0)}
            }
        },
        id="Water Weird from the 5e Database - bp(v1)"
    ),
    pytest.param(
        {
            "url": "talespire://creature-blueprint"
                   "/AgD_AQAAACMAYnI6MDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwZjY2ZjQxMDABAAAAAIkMFyRfeChLqZlY6EwXNW0"
                   "ABAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAD2QgAA9kIAACBBAAAgQQAAIEEAACBBAAAgQQAAIEEAACBBAAAg"
                   "QQAAIEEAACBBAAAgQQAAIEEAACBBAAAgQQAAyEIAAEhDAAAA",
            "assert": {
                "name": "",
                "flying_enabled": False,
                "morph_ids": [(0, "890c1724-5f78-284b-a999-58e84c17356d")],
                "stats": {0: (123.0, 123.0), 8: (100.0, 200.0)}
            }
        },
        id="Orange Meeple Unnamed - bp(v2)"
    ),
    pytest.param(
        {
            "url": "talespire://creature-blueprint"
                   "/AgAKWWVsbG93IE1hbgEAAAAjAGJyOjAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMGZhNmY0MTAwAQAAAADS5CBwM3"
                   "vXRbkNwoZxgJ0UAAQAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAABEIAAEhCAAAgQQAAIEEAACBBAAAgQQAAI"
                   "EEAACBBAAAgQQAAIEEAACBBAAAgQQAAIEEAACBBAAAgQQAAIEEAAKBAAABwQQUAAaYlZoACj_5LujBOvpVTbAU=",
            "assert": {
                "name": "Yellow Man",
                "flying_enabled": True,
                "explicitly_hidden": False,
                "torch_enabled": True,
                "active_emote_ids": ["a6256680-028f-fe4b-ba30-4ebe95536c05"],
                "morph_ids": [(0, "d2e42070-337b-d745-b90d-c28671809d14")],
                "stats": {0: (33.0, 50.0), 8: (5.0, 15.0)}
            }
        },
        id="Yellow Meeple named, flying, torch, prone - bp(v2)"
    ),
    pytest.param(
        {
            "url": "talespire://creature-blueprint"
                   "/AgAKQWxsIE1lZXBsZQgAAAAjAGJyOjAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMGZmNmY0MTAwIwBicjowMDAwMDA"
                   "wMDAwMDAwMDAwMDAwMDAwMDBlZjZmNDEwMCMAYnI6MDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDI3MDQxMDAjAGJy"
                   "OjAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDA0NzA0MTAwIwBicjowMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDBlMjZmND"
                   "EwMCMAYnI6MDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwZjY2ZjQxMDAjAGJyOjAwMDAwMDAwMDAwMDAwMDAwMDAwMDAw"
                   "MGY4NmY0MTAwIwBicjowMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDBmYTZmNDEwMAgAAAAAlalY9W4iP0SsV_AIAIGtP"
                   "AEAAAC0SjjafjeGSogeqBD+9u58AgAAADBr214IKEhFjFU2QS5z9IsDAAAAjj27+80lBEOtly0RMQkpHwQAAADbolu"
                   "04318RYHZE1DqSF1dBQAAAIkMFyRfeChLqZlY6EwXNW0GAAAAuZTaylP3y0+ziTodox+gkgcAAADS5CBwM3vXRbkNw"
                   "oZxgJ0UAwRBEARBEAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAIEEAACBBAAAgQQAAIEEAACBBAAAgQQAAIEEAACBBAAAg"
                   "QQAAIEEAACBBAAAgQQAAIEEAACBBAAAgQQAAIEEAACBBAAAgQQAAAA==",
            "assert": {
                "name": "All Meeple"
            }
        },
        id="All Meeples as Morphs - bp(v2)"
    ),
]


def assert_data(data: dict, assert_dict: dict):
    for key, value in assert_dict.items():
        if key == "stats":
            for stat_index, stat_values in value.items():
                data_stat = data["stats"][stat_index]
                assert (data_stat["value"], data_stat["max"]) == stat_values
        else:
            assert data[key] == value


@pytest.mark.parametrize("input_data", TEST_CASES)
def test_decode(input_data):
    # Test that various parameters decode as expected.
    bp = TSCreature()
    bp.decode_url(input_data["url"])
    assert_data(bp.data, input_data["assert"])


@pytest.mark.parametrize("input_data", TEST_CASES)
def test_encode(input_data):
    # Test that re-encoding the data results in the same URL
    bp = TSCreature()
    original_url = input_data["url"]
    bp.decode_url(original_url)
    new_url = bp.encode_url()
    assert new_url == original_url
