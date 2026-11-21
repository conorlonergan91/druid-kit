"""Shared test setup: a Lua 5.1 runtime (the Lua version WoW uses) with a mocked WoW API.

L = runtime("ui")              # mocks/ui.lua loaded
L.execute(source("DruidKit/DruidKit_Bags.lua"))

DK_LIVE=<live DruidKit folder, absolute path> reads the DruidKit/ files from there instead of the repo copies
(tests/run_all.sh makes a relative one absolute before it changes into tests/).
"""

import os
from pathlib import Path

from lupa.lua51 import LuaRuntime

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent


def addon_dir() -> Path:
    """The DruidKit folder under test: $DK_LIVE if set, else the repository copy."""
    return Path(os.environ.get("DK_LIVE") or ROOT / "DruidKit")


def source(rel: str) -> str:
    """Text of a file in the repository, e.g. source("DruidKit/DruidKit.lua")."""
    if rel.startswith("DruidKit/"):
        return (addon_dir() / rel.removeprefix("DruidKit/")).read_text(encoding="utf-8")
    return (ROOT / rel).read_text(encoding="utf-8")


def mock(name: str) -> str:
    """Text of tests/mocks/<name>.lua."""
    return (HERE / "mocks" / f"{name}.lua").read_text(encoding="utf-8")


def runtime(*mocks: str) -> LuaRuntime:
    """A fresh Lua 5.1 runtime with the named mock files already executed."""
    L = LuaRuntime(unpack_returned_tuples=True)
    for name in mocks:
        L.execute(mock(name))
    return L
