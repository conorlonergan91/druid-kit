"""Route spots vs the quest data: every accept/turn-in/train spot within 1.0 of the NPC or quest spot (RULES v15).

Usage: python3 tools/coordcheck.py ROUTE.py      (prints only problems unless --all)
"""

import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "planner"))
import rk  # noqa: E402
from routeio import load_route  # noqa: E402

ZONE_ID = {v: k for k, v in rk.ZONE_IDS.items()}


def npcs_by_name():
    out = {}
    for v in rk.db()["npcs"].values():
        out.setdefault(v.get("name"), []).append(v)
    return out


def nearest(st, byname):
    """(distance, spot, what) of the data spot closest to the step's goto, or None."""
    z, x, y = st["goto"]
    best = None
    zid = ZONE_ID.get(z)
    for v in byname.get(st.get("npc"), []):
        sp = v.get("spawns")
        for p in sp.get(str(zid), []) if isinstance(sp, dict) else []:
            d = math.hypot(p[0] - x, p[1] - y)
            if best is None or d < best[0]:
                best = (d, p, "npc " + st["npc"])
    q = st.get("q")
    f = rk.quest(q) if q and st["do"] in ("accept", "turnin", "complete") else None
    if f:
        if st["do"] == "accept":
            pts = f["start"]
        elif st["do"] == "turnin":
            pts = f["end"]
        else:
            pts = [f["target_center"]] if f["target_center"] else []
        for p in pts or []:
            if p and p[0] == z and (best is None or "npc" not in best[2]):
                best = (math.hypot(p[1] - x, p[2] - y), list(p[1:]), "quest " + st["do"])
    return best


def check(route_path, show_all=False):
    byname = npcs_by_name()
    bad, n = 0, 0
    for sec in load_route(route_path)["sections"]:
        for st in sec["steps"]:
            n += 1
            if not st.get("goto"):
                continue
            best = nearest(st, byname)
            label = f"step {n} {st['do']} {st.get('name') or st.get('text')}"
            if best and best[0] >= 1.0 and not st.get("party"):
                bad += 1
                z, x, y = st["goto"]
                print(f"CHECK {label}: {z} {x},{y} vs {best[2]} {best[1]} ({best[0]:.1f})")
            elif show_all:
                print(f"ok    {label}" + (f" ({best[0]:.1f})" if best else " (no data)"))
    print(f"coordcheck: {bad} problem(s)")
    return bad


if __name__ == "__main__":
    sys.exit(1 if check(sys.argv[1], "--all" in sys.argv) else 0)
