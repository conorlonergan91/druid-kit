"""tools/save_state.py reads what Lua writes: every string escape (%q included) and inf/nan numbers."""

import math
import sys

from lupa.lua51 import LuaRuntime

from expect import check, done
from wowenv import ROOT

sys.path.insert(0, str(ROOT / "tools"))
import save_state  # noqa: E402


def parse(src, name):
    try:
        return save_state.Parser(src).file()[name]
    except ValueError as e:
        return e


raw = 'Zoë\a\b\f\v\r\n\t\\"end\0'
quoted = LuaRuntime().eval("string.format('%q', ...)", raw)
got = parse(f"S = {quoted}", "S")
check(got == raw, "a %q string (backslash-newline, \\r, \\000) reads back as written", (quoted, got))

got = parse(r'S = "\90\111\195\171 \a\b\f\v\r \"x\" \\"', "S")
check(got == 'Zoë \a\b\f\v\r "x" \\', "\\ddd bytes and control escapes decode", got)

t = parse("T = { a = inf, b = -inf, c = nan, d = 1e1000, e = 0x1F, info = 2 }", "T")
t = t if isinstance(t, dict) else {"a": t, "c": 0}
check(t["a"] == math.inf and t["b"] == -math.inf and t["d"] == math.inf, "inf and -inf read as numbers", t)
check(math.isnan(t["c"]) and t["e"] == 31 and t["info"] == 2, "nan, hex and inf-prefixed keys read", t)
done("py_save_state_test")
