"""Route spots vs the quest data: every accept/turn-in/train spot within 1.0 of the NPC or quest spot (RULES v15).

Usage: python3 tools/coordcheck.py ROUTE.py      (prints only problems unless --all)
"""
import importlib.util
import json
import math
import sys
from pathlib import Path

PLANNER = Path(__file__).resolve().parent.parent / "planner"
sys.path.insert(0, str(PLANNER))
import rk  # noqa: E402

DB = json.load(open(PLANNER / "db.json"))
ZONE_ID = {v: k for k, v in rk.ZONE_IDS.items()}


def zone_id(name):
    return ZONE_ID.get(name)


BYNAME = {}
for v in DB["npcs"].values():
    BYNAME.setdefault(v.get("name"), []).append(v)


def check(route_path, show_all=False):
    spec = importlib.util.spec_from_file_location("r", route_path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    bad, n = 0, 0
    for sec in m.ROUTE["sections"]:
        for st in sec["steps"]:
            n += 1
            g = st.get("goto")
            if not g:
                continue
            z, x, y = g
            best = None
            zid = zone_id(z)
            for v in BYNAME.get(st.get("npc"), []):
                sp = v.get("spawns")
                for p in (sp.get(str(zid), []) if isinstance(sp, dict) else []):
                    d = math.hypot(p[0] - x, p[1] - y)
                    if best is None or d < best[0]:
                        best = (d, p, "npc " + st["npc"])
            q = st.get("q")
            if q and st["do"] in ("accept", "turnin", "complete"):
                f = rk.quest(q)
                if f:
                    pts = f["start"] if st["do"] == "accept" else f["end"] if st["do"] == "turnin" else (
                        [f["target_center"]] if f["target_center"] else [])
                    for p in pts or []:
                        if p and p[0] == z:
                            d = math.hypot(p[1] - x, p[2] - y)
                            if best is None or "npc" not in best[2]:
                                best = (d, list(p[1:]), "quest " + st["do"])
            if best and best[0] >= 1.0 and not st.get("party"):
                bad += 1
                print(f"CHECK step {n} {st['do']} {st.get('name') or st.get('text')}: {z} {x},{y} vs {best[2]} {best[1]} ({best[0]:.1f})")
            elif show_all:
                print(f"ok    step {n} {st['do']} {st.get('name') or st.get('text')}" + (f" ({best[0]:.1f})" if best else " (no data)"))
    print(f"coordcheck: {bad} problem(s)")
    return bad


if __name__ == "__main__":
    sys.exit(1 if check(sys.argv[1], "--all" in sys.argv) else 0)
