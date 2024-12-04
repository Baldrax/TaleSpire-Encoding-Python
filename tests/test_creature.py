import pytest
from ts_encoding.creature import TSCreature

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
                "morph_ids": ["4a6caa43-2713-6d48-8883-36564bb75ce6"],
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
                "morph_ids": ["88ff8a1e-c186-df45-bfb6-6dc63eba08b7"],
                "stats": {0: (99.0, 99.0), 8: (0.0, 0.0)}
            }
        },
        id="Water Weird from the 5e Database - bp(v1)"
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
