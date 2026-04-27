from __future__ import annotations

import os
import sys
from pathlib import Path

def find_talespire_path() -> Path | None:
    # If the path is set in the environment.
    talespire_path_env = os.environ.get("TALESPIRE_PATH")
    if talespire_path_env:
        talespire_path = Path(talespire_path_env)
        if talespire_path.exists():
            return talespire_path

    candidates = []

    if sys.platform.startswith("win"):
        drives = ["C:/", "D:/", "E:/"]
        for drive in drives:
            candidates.extend([
                Path(drive) / "Program Files (x86)/Steam/steamapps/common/TaleSpire",
                Path(drive) / "Program Files/Steam/steamapps/common/TaleSpire",
                Path(drive) / "SteamLibrary/steamapps/common/TaleSpire",
            ])

    elif sys.platform.startswith("linux"):
        home = Path.home()
        candidates.extend([
            home / ".steam/steam/steamapps/common/TaleSpire",
            home / ".local/share/Steam/steamapps/common/TaleSpire",
        ])

    elif sys.platform == "darwin":
        home = Path.home()
        candidates.append(
            home / "Library/Application Support/Steam/steamapps/common/TaleSpire"
        )

    for path in candidates:
        if path.exists():
            return path

    return None
