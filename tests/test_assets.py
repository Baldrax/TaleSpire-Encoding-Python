import pytest

from tests.conftest import find_talespire_path
from ts_encoding import assets

# These tests should ensure that the index.json data stays consistent.
TEST_CASES = [
    pytest.param(
        {
            "uuid": "01c3a210-94fb-449f-8c47-993eda3e7126",
            "assert": {
                "Id": "01c3a210-94fb-449f-8c47-993eda3e7126",
                "Name": "Grass - Lush",
                "ColliderBoundsBound": {"m_Center": {"x": 1.0, "y": 0.25, "z": 1.0},
                                        "m_Extent": {"x": 1.0, "y": 0.25, "z": 1.0}}

            }
        },
        id="Tile: Grass - Lush"
    ),
]

LIBRARY = None

@pytest.fixture(scope="session")
def talespire_path():
    path = find_talespire_path()

    if not path:
        pytest.skip("TaleSpire install not found")

    return path


def test_index_loading(talespire_path):
    index_paths = assets.get_asset_index_paths(talespire_path)

    passed = True

    for path in index_paths:
        if passed:
            passed = path.exists()

    assert passed

def test_library_load(talespire_path):
    global LIBRARY
    LIBRARY = assets.TSAssetLib(talespire_path)

    assert LIBRARY is not None


def assert_data(data: dict, assert_dict: dict):
    for key, value in assert_dict.items():
        assert data[key] == value


@pytest.mark.parametrize("input_data", TEST_CASES)
def test_asset_dict(input_data):
    global LIBRARY
    if LIBRARY is None:
        pytest.skip("Library not loaded")
    assert_data(LIBRARY.asset(input_data["uuid"]).asset_dict, input_data["assert"])