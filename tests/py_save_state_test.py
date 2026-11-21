"""tools/save_state.py reads what Lua writes: every string escape (%q included) and inf/nan numbers."""

import math
import subprocess
import sys
import tempfile
from pathlib import Path

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

# No --char: the newest savedAt wins (old keys stay in the save), and the CLI says which key it read
CP = """ClaudeProgressDB = {
["Char-OldRealm"] = { ["savedAt"] = "2026-11-20 22:10", ["basics"] = { ["level"] = 22, ["zone"] = "Stormwind City" } },
["Char-Realm"] = { ["savedAt"] = "2026-11-21 09:05", ["basics"] = { ["level"] = 24, ["zone"] = "Wetlands" } },
["Char-NoDate"] = { ["basics"] = { ["level"] = 5 } },
}"""
tmp = Path(tempfile.mkdtemp())
(tmp / "cp.lua").write_text(CP, encoding="utf-8")
(tmp / "dk.lua").write_text("DruidKitDB = {}", encoding="utf-8")
s = save_state.state(str(tmp / "cp.lua"), str(tmp / "dk.lua"))
check(s["char"] == "Char-Realm" and s["level"] == 24, "no --char: the key with the newest savedAt", s.get("char"))
s = save_state.state(str(tmp / "cp.lua"), str(tmp / "dk.lua"), "Char-OldRealm")
check(s["level"] == 22, "--char still picks that key", s.get("char"))
(tmp / "cp2.lua").write_text('ClaudeProgressDB = { ["A-R"] = { ["basics"] = {} }, ["B-R"] = { ["basics"] = {} } }')
s = save_state.state(str(tmp / "cp2.lua"), str(tmp / "dk.lua"))
check(s["char"] == "A-R", "no savedAt anywhere: the first key", s.get("char"))
r = subprocess.run(
    [sys.executable, str(ROOT / "tools/save_state.py"), str(tmp / "cp.lua"), str(tmp / "dk.lua")],
    capture_output=True,
    text=True,
)
check(r.returncode == 0 and '"Char-Realm"' in r.stderr and "2026-11-21 09:05" in r.stderr, "stderr names key", r.stderr)
check(r.returncode == 0 and r.stdout.startswith("{"), "stdout is only JSON", r.stdout[:80])
done("py_save_state_test")
