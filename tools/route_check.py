"""Check a route's travel against what the character can really use: the hearthstone and known flight paths.

Usage: python3 tools/route_check.py ROUTE.py [--home "Stormwind"] [--flights "Stormwind, Elwynn;Thelsamar, Loch Modan"]

--home and --flights come from the save (ClaudeProgress `travel.home`, `travel.flights`). Without --flights the
starting flight paths are unknown and only learned-in-route paths count.

Errors (exit 1):
  - a hearth step to a town the hearthstone isn't set to (no earlier `home` step there, and not the save's home)
  - a fly step to, or from, a flight path that isn't known (no earlier `fp` step, not in the save)
Warnings:
  - the route walks through a town with a flight master without an `fp` step there
  - a note step that sets the hearth or learns a flight path (use do="home" / do="fp" so the step ticks itself)
"""

import importlib.util
import json
import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
TRAVEL_FILE = (
    next(p for p in (HERE.parent / "planner", HERE.parent / "routekit", HERE) if (p / "travel.json").exists())
    / "travel.json"
)
TRAVEL = json.loads(TRAVEL_FILE.read_text(encoding="utf-8"))
NEAR_YD = 300


def load(path):
    spec = importlib.util.spec_from_file_location("route", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.ROUTE


def town_of(text):
    """The travel.json town a free-text place names ("Menethil Harbor", "Thelsamar, Loch Modan")."""
    t = (text or "").lower().split(",")[0].strip()
    if not t:
        return None
    for name in sorted(TRAVEL["towns"], key=len, reverse=True):
        n = name.lower()
        if n in t or t in n:
            return name
    return None


def town_near(goto):
    if not goto or goto[0] not in TRAVEL["zone_yards"]:
        return None
    w, h = TRAVEL["zone_yards"][goto[0]]
    best, bd = None, 1e18
    for name, t in TRAVEL["towns"].items():
        if t["zone"] != goto[0]:
            continue
        d = math.hypot((goto[1] - t["x"]) / 100 * w, (goto[2] - t["y"]) / 100 * h)
        if d < bd:
            best, bd = name, d
    return best if bd <= NEAR_YD else None


def check(route, home=None, flights=None):
    errors, warnings = [], []
    home = town_of(home) if home else None
    known = {town_of(f) for f in (flights or []) if town_of(f)}
    start_unknown = flights is None
    warned = set()
    route_fp = {town_of(st.get("to")) for sec in route["sections"] for st in sec["steps"] if st.get("do") == "fp"}
    n = 0
    for sec in route["sections"]:
        for st in sec["steps"]:
            n += 1
            d = st.get("do")
            label = f"step {n} ({sec['title']})"
            text = (st.get("text") or "").lower()
            if d == "note" and "hearth" in text and ("set" in text or "bind" in text):
                warnings.append(f"{label}: sets the hearth in a note; use do='home', to='<town>' so it ticks itself")
            if d == "note" and "flight path" in text and ("learn" in text or "pick up" in text):
                warnings.append(f"{label}: learns a flight path in a note; use do='fp', to='<town>'")
            if d == "home":
                home = town_of(st.get("to")) or home
            elif d == "fp":
                t = town_of(st.get("to"))
                if t and not TRAVEL["towns"][t].get("fm"):
                    warnings.append(f"{label}: {t} has no flight master in planner/travel.json")
                if t:
                    known.add(t)
            elif d == "hearth":
                t = town_of(st.get("to"))
                if not home:
                    errors.append(
                        f"{label}: hearth to {st.get('to')}, but no hearth is set (add a 'home' step first, "
                        "or pass --home from the save)"
                    )
                elif t and t != home:
                    errors.append(f"{label}: hearth to {st.get('to')}, but the hearthstone is set to {home}")
            elif d == "fly":
                for what, place in (("to", st.get("to")), ("from", st.get("where"))):
                    t = town_of(place) if what == "to" or "flight master" in (place or "").lower() else None
                    if t and t not in known and start_unknown:
                        warnings.append(
                            f"{label}: fly {what} {t}: not learned in this route (fine if the save shows you know it)"
                        )
                    elif t and t not in known:
                        errors.append(
                            f"{label}: fly {what} {t}, but that flight path isn't learned (add an 'fp' step "
                            "when the route first passes it, or walk/boat)"
                        )
            at = town_near(st.get("goto")) or (town_of(st.get("to")) if d in ("goto", "fly", "hearth") else None)
            if at and TRAVEL["towns"][at].get("fm") and at not in known and at not in route_fp and at not in warned:
                warned.add(at)
                hint = " (unless the save shows you know it)" if start_unknown else ""
                warnings.append(
                    f"{label}: the route reaches {at}, which has a flight master, but never learns that "
                    f"flight path: add an 'fp' step{hint}"
                )
    return errors, warnings


def main(argv):
    route = load(argv[1])
    home = argv[argv.index("--home") + 1] if "--home" in argv else None
    flights = argv[argv.index("--flights") + 1].split(";") if "--flights" in argv else None
    errors, warnings = check(route, home, flights)
    for e in errors:
        print("ERROR  " + e)
    for w in warnings:
        print("warn   " + w)
    if not errors and not warnings:
        print("travel ok: every hearth and flight is usable")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
