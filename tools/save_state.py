"""Read the game's SavedVariables (ClaudeProgress.lua + DruidKit.lua) into the state an update needs.

Pure Python (no lupa), so it runs on the player's Mac as well as in the cloud.

Usage: python3 tools/save_state.py ClaudeProgress.lua DruidKit.lua [--char "Name-Realm"]  -> JSON on stdout

State: level, xp, zone, subzone, x, y, gold, bags_free, quest log (id -> title, complete), completed quest ids,
travel (home, flights, hearthCooldown), route (id, step, manual step indexes, skipped and passed quests).
"""

import json
import re
import sys

TOKEN = re.compile(
    r"""\s*(?:
        (?P<comment>--[^\n]*)
      | (?P<str>"(?:[^"\\]|\\.)*")
      | (?P<num>-?\d+(?:\.\d+)?(?:[eE][-+]?\d+)?)
      | (?P<word>[A-Za-z_][A-Za-z0-9_]*)
      | (?P<sym>[{}\[\]=,;])
    )""",
    re.X,
)


def tokens(src):
    pos = 0
    while pos < len(src):
        m = TOKEN.match(src, pos)
        if not m or m.end() == pos:
            if src[pos:].strip() == "":
                return
            raise ValueError(f"can't read SavedVariables at {pos}: {src[pos : pos + 40]!r}")
        pos = m.end()
        kind = m.lastgroup
        if kind == "comment":
            continue
        yield kind, m.group(kind)


def _unquote(s):
    body = s[1:-1]
    return re.sub(r"\\(.)", lambda m: {"n": "\n", "t": "\t"}.get(m.group(1), m.group(1)), body)


class Parser:
    def __init__(self, src):
        self.toks = list(tokens(src))
        self.i = 0

    def peek(self):
        return self.toks[self.i] if self.i < len(self.toks) else (None, None)

    def take(self, want=None):
        t = self.toks[self.i]
        if want and t[1] != want:
            raise ValueError(f"expected {want}, got {t[1]}")
        self.i += 1
        return t

    def value(self):
        kind, v = self.take()
        if kind == "str":
            return _unquote(v)
        if kind == "num":
            return float(v) if any(c in v for c in ".eE") else int(v)
        if kind == "word":
            return {"true": True, "false": False, "nil": None}.get(v, v)
        if v == "{":
            return self.table()
        raise ValueError(f"unexpected {v}")

    def table(self):
        out, n = {}, 0
        while self.peek()[1] != "}":
            if self.peek()[1] == "[":
                self.take("[")
                key = self.value()
                self.take("]")
                self.take("=")
                out[key] = self.value()
            elif self.peek()[0] == "word" and self.toks[self.i + 1][1] == "=":
                key = self.take()[1]
                self.take("=")
                out[key] = self.value()
            else:
                n += 1
                out[n] = self.value()
            if self.peek()[1] in (",", ";"):
                self.take()
        self.take("}")
        return out

    def file(self):
        out = {}
        while self.i < len(self.toks):
            name = self.take()[1]
            self.take("=")
            out[name] = self.value()
        return out


def read_lua(path):
    with open(path, encoding="utf-8") as f:
        return Parser(f.read()).file()


def as_list(t):
    """A Lua array (dict with 1..n keys) as a Python list."""
    if isinstance(t, list):
        return t
    if not isinstance(t, dict):
        return []
    return [t[k] for k in sorted(k for k in t if isinstance(k, int))]


def state(claude_progress, druidkit, char=None):
    cp = read_lua(claude_progress).get("ClaudeProgressDB", {})
    chars = [k for k, v in cp.items() if isinstance(v, dict) and "basics" in v]
    key = char or (chars[0] if chars else None)
    me = cp.get(key, {})
    b = me.get("basics", {})
    log = {}
    for q in as_list(me.get("quests")):
        if isinstance(q, dict) and q.get("id"):
            objs = as_list(q.get("objectives"))
            log[int(q["id"])] = {
                "title": q.get("title"),
                "complete": bool(q.get("isComplete") or q.get("complete"))
                or (bool(objs) and all(o.get("done") for o in objs if isinstance(o, dict))),
            }
    done = sorted(int(k) for k in ((me.get("completed") or {}).get("quests") or {}) if isinstance(k, int))
    travel = me.get("travel") or {}
    dk = read_lua(druidkit).get("DruidKitDB", {})
    return {
        "char": key,
        "savedAt": me.get("savedAt"),
        "level": b.get("level"),
        "xp": b.get("xp"),
        "xpMax": b.get("xpMax"),
        "zone": b.get("zone"),
        "subzone": b.get("subzone"),
        "x": b.get("x"),
        "y": b.get("y"),
        "gold": b.get("gold"),
        "bags_free": (me.get("bags") or {}).get("free"),
        "log": log,
        "done": done,
        "travel": {
            "home": travel.get("home"),
            "hearthCooldown": travel.get("hearthCooldown"),
            "flights": as_list(travel.get("flights")),
            "flightsKnown": travel.get("flightsKnown"),
        },
        "route": {
            "id": dk.get("routeId"),
            "step": dk.get("routeStep"),
            "manual": sorted(k for k, v in (dk.get("manual") or {}).items() if v),
            "skipped": sorted(str(k) for k in (dk.get("skipQ") or {})),
            "passed": sorted(str(k) for k in (dk.get("passedQ") or {})),
        },
    }


if __name__ == "__main__":
    a = sys.argv
    out = state(a[1], a[2], a[a.index("--char") + 1] if "--char" in a else None)
    print(json.dumps(out, ensure_ascii=False, indent=1))
