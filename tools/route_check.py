"""Check a route's travel against what the character can really use: the hearthstone and known flight paths.

Usage: python3 tools/route_check.py ROUTE.py [--home "Stormwind"] [--flights "Stormwind, Elwynn;Thelsamar, Loch Modan"]

--home and --flights come from the save (ClaudeProgress `travel.home`, `travel.flights`). Without --flights the
starting flight paths are unknown and only learned-in-route paths count.

Errors (exit 1):
  - a hearth step to a town the hearthstone isn't set to (no earlier `home` step there, and not the save's home)
  - a fly step to, or from, a flight path that isn't known (no earlier `fp` step, not in the save)
  - a fly step with no direct flight between its two towns (each flight hop is its own step)
Warnings:
  - the route walks through a town with a flight master without an `fp` step there
  - a note step that sets the hearth or learns a flight path (use do="home" / do="fp" so the step ticks itself)
  - a boat, tram, portal or zeppelin step without `how` (where to board, which ship, the wait, where it lands)
"""

import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "planner"))
import rk  # noqa: E402
from routeio import load_route  # noqa: E402

TRAVEL = rk.TRAVEL
NEAR_YD = 300
town_of = rk.town_in


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


TRANSPORT = ("boat", "ship", "tram", "portal", "zeppelin", "ferry")


def flight_hops(a, b):
    """Towns on the shortest chain of direct flights from a to b ([a, ..., b]), or None."""
    links = {}
    for e in TRAVEL["edges"]:
        if e.get("how") == "flight":
            links.setdefault(e["a"], set()).add(e["b"])
            if not e.get("oneway"):
                links.setdefault(e["b"], set()).add(e["a"])
    paths, seen = [[a]], {a}
    while paths:
        nxt = []
        for p in paths:
            if p[-1] == b:
                return p
            for v in links.get(p[-1], ()):
                if v not in seen:
                    seen.add(v)
                    nxt.append(p + [v])
        paths = nxt
    return None


def zone_town(text):
    """The only town of a zone named in the text ("Moonglade flight master" -> Nighthaven)."""
    t = (text or "").lower()
    for zone in TRAVEL["zone_yards"]:
        if zone.lower() in t:
            inside = [n for n, v in TRAVEL["towns"].items() if v["zone"] == zone]
            if len(inside) == 1:
                return inside[0]
    return None


def check(route, home=None, flights=None):
    errors, warnings = [], []
    home = town_of(home) if home else None
    known = {town_of(f) for f in (flights or []) if town_of(f)}
    known |= {n for n, v in TRAVEL["towns"].items() if v.get("always_known")}
    start_unknown = flights is None
    warned = set()
    last_town = None
    flat = [st for sec in route["sections"] for st in sec["steps"]]
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
            if d == "note" and text.startswith("abandon"):
                warnings.append(f"{label}: abandons quests in a note; use do='abandon', qs=[ids] so it ticks itself")
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
                fm_text = st.get("where") if "flight master" in (st.get("where") or "").lower() else None
                origin = town_of(fm_text) or zone_town(fm_text)
                origin = origin or town_near(st.get("goto")) or last_town
                dest = town_of(st.get("to"))
                hops = flight_hops(origin, dest) if origin and dest and origin != dest else None
                if origin and dest and origin != dest and (not hops or len(hops) > 2):
                    chain = " -> ".join(hops) if hops else "none in planner/travel.json"

                    # The game flies on through known flight points by itself: pick the far town on the map.
                    # ...but not on a special one-way flight (Nighthaven's druid flight only goes to Rut'theran)
                    def regular(x, y):
                        return any(
                            {e["a"], e["b"]} == {x, y} and e.get("how") == "flight" and not e.get("oneway")
                            for e in TRAVEL["edges"]
                        )

                    via_known = (
                        hops
                        and all(h in known for h in hops[1:-1])
                        and all(regular(hops[i], hops[i + 1]) for i in range(len(hops) - 1))
                    )
                    if via_known:
                        warnings.append(f"{label}: one flight through {chain} (the game flies on by itself)")
                    else:
                        errors.append(
                            f"{label}: no flight {origin} -> {dest} (chain: {chain}); a flight point on the way "
                            "is not learned, or there is no chain"
                        )
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
            words = " ".join(str(st.get(k) or "") for k in ("text", "where")).lower()
            if d == "goto" and not st.get("goto") and not any(nx.get("goto") for nx in flat[n : n + 4]):
                warnings.append(f"{label}: no map spot here or in the next 4 steps: the arrow has nothing to show")
            if d == "goto" and any(w in words for w in TRANSPORT) and not st.get("how"):
                warnings.append(
                    f"{label}: transport step without how: say where to board (pier or platform, with goto "
                    "when the spot is verified), which ship or portal, the usual wait and where it lands"
                )
            at = town_near(st.get("goto")) or (town_of(st.get("to")) if d in ("goto", "fly", "hearth") else None)
            if at or (st.get("goto") and zone_town(st["goto"][0])):
                last_town = at or zone_town(st["goto"][0])
            if d in ("fly", "hearth", "goto") and town_of(st.get("to")):
                last_town = town_of(st.get("to"))
            if at and TRAVEL["towns"][at].get("fm") and at not in known and at not in route_fp and at not in warned:
                warned.add(at)
                hint = " (unless the save shows you know it)" if start_unknown else ""
                warnings.append(
                    f"{label}: the route reaches {at}, which has a flight master, but never learns that "
                    f"flight path: add an 'fp' step{hint}"
                )
    return errors, warnings


def main(argv):
    route = load_route(argv[1])
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
