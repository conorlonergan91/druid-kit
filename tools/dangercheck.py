"""Solo steps: hostile monsters 3+ levels above the player within 3 map units of the step spot (RULES v16).

Usage: python3 tools/dangercheck.py ROUTE.py [PLAYER_LEVEL]
"""

import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "planner"))
import rk  # noqa: E402
from routeio import load_route  # noqa: E402

CAPITALS = ("Stormwind City", "Ironforge", "Darnassus", "Orgrimmar", "Thunder Bluff", "Undercity")
ZID = {v: k for k, v in rk.ZONE_IDS.items()}


def hostile_mobs():
    mobs = []
    for v in rk.db()["npcs"].values():
        lvl = v.get("minLevel")
        if v.get("friendlyToFaction") or v.get("npcFlags") or not lvl or lvl > 70 or v.get("rank"):
            continue
        sp = v.get("spawns")
        if isinstance(sp, dict):
            for z, pts in sp.items():
                mobs.extend((int(z), p[0], p[1], lvl, v.get("name", "?")) for p in pts)
    return mobs


def check(route, lvl, mobs):
    out, n = [], 0
    for sec in route["sections"]:
        for st in sec["steps"]:
            n += 1
            if st.get("party") or ("group" in sec["title"].lower() and st["do"] == "complete"):
                continue
            if st["do"] == "level":
                lvl = max(lvl, st["level"] - 1)
            g = st.get("goto")
            if not g or g[0] not in ZID or g[0] in CAPITALS:
                continue
            bad = {}
            for z, x, y, mob_lvl, name in mobs:
                # 15+ above: town NPCs and guards
                if z == ZID[g[0]] and lvl + 3 <= mob_lvl < lvl + 15 and math.hypot(x - g[1], y - g[2]) < 3:
                    bad[name] = mob_lvl
            if bad:
                worst = sorted(bad.items(), key=lambda t: -t[1])[:5]
                out.append(f"{n} {st.get('name') or st.get('text')} {g} | lvl {lvl} | {worst}")
    return out


def main(argv):
    lvl = float(argv[2]) if len(argv) > 2 else 22
    for line in check(load_route(argv[1]), lvl, hostile_mobs()):
        print(line)


if __name__ == "__main__":
    main(sys.argv)
