"""
Tools for reading in TaleSpire assets.
These require a path to a valid TaleSpire install.
It utilizes the `index.json` files within the installed location to get asset information.
"""
from __future__ import annotations

import json

from pathlib import Path

from ts_encoding import InvalidTaleSpireDirectory, InvalidAssetType


def get_asset_index_paths(ts_basedir: Path | str) -> list[Path]:
    """
    Given the base TaleSpire Directory get a list of all the paths to index.json files.

    Args:
        ts_basedir: The base directory that TaleSpire is installed in.
    """
    ts_base_path = Path(str(ts_basedir))
    taleweaver_dir = ts_base_path / "Taleweaver"

    if taleweaver_dir.is_dir():
        return list(taleweaver_dir.rglob("index.json"))
    else:
        raise InvalidTaleSpireDirectory(f"The supplied TaleSpire directory is not valid:\n\t{ts_base_path}")


def read_index_file(index_file: Path | str) -> dict:
    """
    Read in the given index file and return it as a dictionary.

    Args:
        index_file: The TaleSpire index.json file to be read.
    """
    index_file_path = Path(str(index_file))
    with index_file_path.open("r", encoding="utf-8") as f:
        index_dict = json.load(f)

    return index_dict


def get_index_dicts(ts_basedir: Path | str) -> dict:
    """
    Given the base TaleSpire directory return a dictionary containing
    all the content pack asset indexes as dictionaries.

    Args:
        ts_basedir: The base directory that TaleSpire is installed in.
    """
    index_files = get_asset_index_paths(ts_basedir)

    index_dicts = {}

    for index_file in index_files:
        index_dict = read_index_file(index_file)
        index_name = index_dict["Name"]
        index_dicts[index_name] = {"path": str(index_file), "index": index_dict}

    return index_dicts


class TSAssetLib:

    # This is the default list of asset loaded as well as the valid types excepted.
    default_asset_filter = ["Tiles", "Props", "Creatures", "Music"]

    def __init__(self, ts_basedir, asset_filter: list[str] | None = None):
        """
        TaleSpire Asset Library
        This reads in all the TaleSpire assets and stores them both in index form and by UUID.

        A filter can be set to limit what types of assets are stored.
        Valid types are: ["Tiles", "Props", "Creatures", "Music"]
        The default is all asset types.

        Args:
            ts_basedir: The base directory that TaleSpire is installed in.
            asset_filter: A list of asset types to use as a filter.
        """
        self.index_dicts = get_index_dicts(ts_basedir)
        self.asset_filter = asset_filter if asset_filter else self.default_asset_filter
        self.index_names = list(self.index_dicts.keys())
        self.asset_uuid_dict: dict[str, TSAsset] = {}
        self._build_asset_uuid_dict()

    def _build_asset_uuid_dict(self) -> None:
        for index_name in self.index_names:
            index_path = Path(self.index_dicts[index_name]["path"])
            index_dict = self.index_dicts[index_name]["index"]

            icon_atlases = []
            for atlas_entry in index_dict["IconsAtlases"]:
                icon_atlases.append(atlas_entry["Path"])

            for asset_type in self.asset_filter:
                asset_type = asset_type.title()
                if asset_type not in self.default_asset_filter:
                    raise InvalidAssetType(
                        f"Invalid Asset Filter: {asset_type}\nValid types are: {self.default_asset_filter}"
                    )

                for asset_dict in self.index_dicts[index_name]["index"][asset_type]:
                    if "Icon" in asset_dict:
                        asset = TSIconAsset(asset_dict, asset_type)
                        atlas_index = asset_dict["Icon"]["AtlasIndex"]
                        asset.icon_atlas = str(index_path.parent / icon_atlases[atlas_index])
                    else:
                        asset = TSAsset(asset_dict, asset_type)

                    self.asset_uuid_dict[asset.id] = asset

    def asset(self, asset_uuid: str) -> TSAsset:
        """
        Given a UUID return the asset.

        Args:
            asset_uuid: The TaleSpire asset UUID
        """
        asset = self.asset_uuid_dict.get(asset_uuid, None)
        return asset

    def assets(self) -> list[TSAsset]:
        """Returns a list of all the assets in the library."""
        return list(self.asset_uuid_dict.values())


class TSAsset:

    def __init__(self, asset_dict, asset_type):
        self.asset_dict = asset_dict
        self.asset_type = asset_type
        self.id = asset_dict["Id"].lower()
        self.name = asset_dict["Name"]
        self.deprecated = asset_dict["IsDeprecated"] == 1


class TSIconAsset(TSAsset):

    def __init__(self, asset_dict, asset_type):
        super().__init__(asset_dict, asset_type)
        self.icon_atlas_index = asset_dict["Icon"]["AtlasIndex"]
        self.icon_atlas = ""
        atlas_region = asset_dict["Icon"]["Region"]
        self.atlas_region = (
            atlas_region["x"],
            atlas_region["y"],
            atlas_region["width"],
            atlas_region["height"]
        )