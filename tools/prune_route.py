"""Tidy a route on update: drop every step the player has already done or passed, so the step window and the Now
tab start at the real next step when they log in.

Usage: python3 tools/prune_route.py ROUTE.py STATE.json OUT.py [--id NEW_ID]
       STATE.json comes from tools/save_state.py.

Dropped:
  - with the same route id as the save: every step before the saved step (already done, ticked or passed)
  - accept: quest in the log or handed in · turnin: handed in · complete: handed in, or complete in the log
  - fp: flight path known · home: hearthstone already there · abandon: none of its quests in the log
  - level: level reached · any step of a quest the player skipped (Skip button; the re-plan decides on those)
  - notes, walks, flights before the last dropped hand-in (behind the player)
  - sections left empty
The pruned route gets a new id (default: old id + ".t<HHMM>") so the tracker starts at its first step; the tracker
still catches up by itself if the save moved on.
"""

import json
import pprint
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "planner"))
import rk  # noqa: E402
from routeio import load_module  # noqa: E402

TRAVEL_STEPS = ("note", "goto", "fly", "hearth", "train", "fp", "home", "level")


def load(path):
    mod = load_module(path)
    return mod.ROUTE, (mod.__doc__ or "").strip()


def _same(a, b):
    ta, tb = rk.town_in(a), rk.town_in(b)
    if ta or tb:
        return ta == tb
    return bool(a and b) and a.strip().lower() == b.strip().lower()


def done_by_state(st, s):
    d, q = st.get("do"), st.get("q")
    log, done = s.get("log", {}), set(s.get("done", []))
    in_log = q is not None and str(q) in {str(k) for k in log}
    entry = log.get(str(q)) or log.get(q) or {}
    if q is not None and str(q) in set(s.get("route", {}).get("skipped", [])):
        return True
    if d == "accept":
        return in_log or q in done
    if d == "turnin":
        return q in done
    if d == "complete":
        return q in done or bool(entry.get("complete"))
    if d == "fp":
        return any(_same(f.split(",")[0], st.get("to")) for f in s.get("travel", {}).get("flights", []))
    if d == "home":
        return _same(s.get("travel", {}).get("home"), st.get("to"))
    if d == "abandon":
        return not any(str(x) in {str(k) for k in log} for x in (st.get("qs") or [q]))
    if d == "level":
        return (s.get("level") or 0) >= (st.get("level") or 999)
    return False


def prune(route, s):
    flat = [(si, st) for si, sec in enumerate(route["sections"]) for st in sec["steps"]]
    keep = [True] * len(flat)
    if s.get("route", {}).get("id") == route["id"] and s["route"].get("step"):
        for i in range(min(len(flat), s["route"]["step"] - 1)):
            keep[i] = False
    for i, (_, st) in enumerate(flat):
        if keep[i] and done_by_state(st, s):
            keep[i] = False
    # Travel is behind the player only up to the last hand-in of the done run at the start of the route; a quest
    # skipped or handed in out of order further on doesn't mean the walks before it were made.
    last = -1
    for i, (_, st) in enumerate(flat):
        if keep[i] and st.get("do") not in TRAVEL_STEPS:
            break
        if not keep[i] and st.get("do") == "turnin":
            last = i
    for i in range(last):
        if flat[i][1].get("do") in TRAVEL_STEPS:
            keep[i] = False
    out = {k: v for k, v in route.items() if k != "sections"}
    out["sections"] = []
    for si, sec in enumerate(route["sections"]):
        steps = [st for i, (sj, st) in enumerate(flat) if sj == si and keep[i]]
        if steps:
            out["sections"].append({**{k: v for k, v in sec.items() if k != "steps"}, "steps": steps})
    return out, len(flat) - sum(keep)


def main(argv):
    route, doc = load(argv[1])
    with open(argv[2], encoding="utf-8") as f:
        s = json.load(f)
    pruned, n = prune(route, s)
    base = route["id"].split(".t")[0]
    pruned["id"] = argv[argv.index("--id") + 1] if "--id" in argv else f"{base}.t{time.strftime('%H%M')}"
    head = f"Tidied {time.strftime('%d %b %H:%M')}: {n} done steps removed (tools/prune_route.py)."
    text = f'"""{doc}\n\n{head}\n"""\n\nROUTE = ' + pprint.pformat(pruned, width=118, sort_dicts=False) + "\n"
    with open(argv[3], "w", encoding="utf-8") as f:
        f.write(text)
    left = sum(len(sec["steps"]) for sec in pruned["sections"])
    print(f"{n} done steps removed, {left} left in {len(pruned['sections'])} sections; new id {pruned['id']}")


if __name__ == "__main__":
    main(sys.argv)
