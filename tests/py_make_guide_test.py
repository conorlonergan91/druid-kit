"""Strings tools/make_guide.py and tools/dungeon_data.py write must read back unchanged in Lua 5.1."""

import sys

from lupa.lua51 import LuaRuntime

from expect import check, done
from wowenv import ROOT

sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT / "planner"))
import dungeon_data  # noqa: E402
import make_guide  # noqa: E402

TRICKY = [
    "Buy [Light Leather]",
    "[[x]]",
    "a]]b",
    "a]=]b]==]",
    "[=[",
    "]",
    "[",
    'say "hi"',
    "back\\slash\\",
    "two\nlines\r\n",
    "nul\0after",
    "nul\x001digit",
    "tab\tbell\x07del\x7f",
    "|cffffd100Gold|r → Höhle",
    "",
]
L = LuaRuntime()
for s in TRICKY:
    for name, quote in (("make_guide", make_guide.lua_str), ("dungeon_data", dungeon_data.lua)):
        src = quote(s)
        try:
            got = L.execute("return " + src)
        except Exception as e:
            got = e
        check(got == s, f"{name} round-trips {s!r}", (src, got))
key = make_guide.route_lua({"id": "r", "sections": [], "items": {"[Key]": {"action": "bank", "why": "x]"}}})
check(L.execute("\n".join(key) + "\nreturn DruidKitRoute.items['[Key]'].why") == "x]", "item keys in brackets", key)
done("py_make_guide_test")
