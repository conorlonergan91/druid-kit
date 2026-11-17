"""Quest pack for the blind planner: every quest a Night Elf Druid can do to ~34 nearby, from the routekit DB."""

import csv
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import rk  # noqa: E402

ZONES = {
    "Teldrassil",
    "Darnassus",
    "Darkshore",
    "Moonglade",
    "Ashenvale",
    "Stormwind City",
    "Elwynn Forest",
    "Westfall",
    "Redridge Mountains",
    "Loch Modan",
    "Wetlands",
    "Dun Morogh",
    "Ironforge",
    "Duskwood",
    "Stonetalon Mountains",
    "The Deadmines",
    "Blackfathom Deeps",
    "The Stockade",
    "class/other",
    "Hillsbrad Foothills",
    "Arathi Highlands",
    "Stranglethorn Vale",
    "Desolace",
    "Thousand Needles",
    "Alterac Mountains",
    "The Barrens",
    "Gnomeregan",
    "Razorfen Kraul",
    "Scarlet Monastery",
}
ALIAS = {
    "Elwynn": "Elwynn Forest",
    "Redridge": "Redridge Mountains",
    "Stormwind": "Stormwind City",
    "Stonetalon": "Stonetalon Mountains",
}
rows = []
for k in rk.db()["quests"]:
    q = rk.quest(int(k))
    if not q or not rk.eligible(q) or q["level"] > 34 or q["min"] > 30 or q["repeatable"]:
        continue
    z = ALIAS.get(q["zone"], q["zone"])
    s, e = (q["start"] or [None])[0], (q["end"] or [None])[0]
    sz = ALIAS.get(s[0], s[0]) if s else ""
    ez = ALIAS.get(e[0], e[0]) if e else ""
    if z not in ZONES and sz not in ZONES:
        continue
    if z == "class/other":
        z = sz or ez
    rows.append(
        {
            "id": q["id"],
            "name": q["name"],
            "level": q["level"],
            "min_level": q["min"],
            "zone": z,
            "class_quest": "druid" if q["classes"] and q["classes"] & 1024 else "",
            "starts": "item" if q["start_item"] else ("npc" if s else ""),
            "start_zone": sz,
            "start_xy": f"{s[1]},{s[2]}" if s else "",
            "end_zone": ez,
            "end_xy": f"{e[1]},{e[2]}" if e else "",
            "requires_quests": " ".join(map(str, (q["pre_all"] or []) + (q["pre_any"] or []))),
            "next_in_chain": q["next"] or "",
            "xp": q["xp"],
            "objectives": q["text"],
        }
    )
with open(
    sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(os.path.abspath(__file__)), "quests.csv"),
    "w",
    newline="",
    encoding="utf-8",
) as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0]))
    w.writeheader()
    w.writerows(sorted(rows, key=lambda r: (r["level"], r["id"])))
print(len(rows))
