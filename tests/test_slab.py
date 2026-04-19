import pytest

from ts_encoding.slab import TSSlab

TEST_CASES = [
    pytest.param(
        {
            "slab_code": "H4sIAAAAAAAACjv369xFJgZGBgYGgUWHGX9Pme/S4z7T7pZdoRonUGwCSIKhgRFMS0L4DTwMDCcYwOIsDBDADOZLQsRB8"
                         "gxQPgOcDwD7jJ0vaAAAAA==",
            "assert": {
                "magic_num": 3520002766,
                "version": 2,
                "layout_count": 1,
                "num_creatures": 0
            }
        },
        id="9x9 Test Ground - slab(v2)"
    ),
    pytest.param(
        {
            "slab_code": "H4sIAAAAAAAACzv369xFRgZuhn3r5HqWHr3m0rZX1Ofl3UZZOYa7knuW/uxZevWd0/zQfxqdZkcFWIBi1eoWR8USf/gvm"
                         "ayqeoMhdDdILKHb5/ijpxPd9yk9WDFvYtlWRqCY6EnvC1lls/1nfdh3y1RBNwYktu5C37P7s4L91mscuGfIfuYPSG9Ind"
                         "Bb0dj5DpuuTXt84246WOzpnkf/gv+s9tuzi7eq+IW3J0jv+Z3rGC/JPHafc2OFV0DT3WCQ2I6Xyx0+Xdf2m7R+w//PTMI"
                         "ZIL1coqk+bnrnHWe+l5Q1vJnxgAMoxsAg4MjA0GDHwHAARNtD2EB6Zp09Qm4DqpwwjxNCbgGqHBjA5CZgkXvggNW+LSf2"
                         "IuQ24NGHZh8TshyafY+b04HqsdsH1rcAu337zQsQcmj2/QexF2C3DwwcsNuHIofNfw7Y7UORQ7PvM58tgo9uHxxjsa9hP"
                         "4KPzT4YH8N/WxBx24AnjtDkfvz9jwgzNLl6ZP+hybG0pCPxscQf2B+Yfs984oWQwxbWMDmsft+P3e/wcMN0S8dcIJ0A9A"
                         "MHEM8ByjEA5SbYg2lpW3uE3BJUObAZE7DrA4MJ2PUdmg/kXwCKPwDy10DlHJD0weSmYJE7YI9VX1SFPUIOTd97SSeIHzK"
                         "Q3HnADkzbvtsHcWcEkjsZIHINQAj2I8icDRjx9+N/PVQONax54GkJU44DRQ7VTJYP//9D/B7ggPBfgx0irGFyU1DlkqdK"
                         "QvyORa4eFmZYzEy1LoCIg/y+DJovQH6HpRlQuCQghRnMLTAzDTDt4xdogLgTi9x/WNwaYPEfsploclt/7IPkPyzxwADLf"
                         "9jkYGUdZjyg6sNVzoPksOWxBdjlwPndAbscJL/bY9cHCrMGB5CDIHIHYGwHAFBW+IfEBwAA",
            "assert": {
                "magic_num": 3520002766,
                "version": 1,
                "layout_count": 11
            }
        },
        id="Elemental Summoning Pillars (Oceanlord) - slab(v1)"
    )
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
    slab = TSSlab()
    slab.decode_slab(input_data["slab_code"])
    assert_data(slab.data, input_data["assert"])


@pytest.mark.parametrize("input_data", TEST_CASES)
def test_encode(input_data):
    # Test that decoding and re-encoding the data results in the same results
    slab = TSSlab()
    original_slab_code = input_data["slab_code"]
    slab.decode_slab(original_slab_code)
    new_slab_code = slab.encode_slab()

    new_slab = TSSlab()
    new_slab.decode_slab(new_slab_code)
    assert_data(new_slab.data, input_data["assert"])
