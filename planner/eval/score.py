"""Score a generated Night Elf Druid 1-20 plan against the reference.

Only quests present in the public quest pack count (the generator cannot know the others).
  selection 45%  F1 of handed-in quests
  order     25%  Kendall tau of hand-in order over shared quests, mapped to 0-1
  zones     20%  similarity of the zone sequence (runs of hand-in zones), normalised edit distance
  hearth    10%  Jaccard of hearthstone bind places
Usage: python3 score.py plan.json [--detail]
"""

import csv
import json
import os
import sys
from pathlib import Path

HERE = os.path.dirname(os.path.abspath(__file__))
REF = json.loads(Path(os.environ.get("RK_REFERENCE", os.path.join(HERE, "reference.json"))).read_text(encoding="utf-8"))
PACK = {
    int(r["id"]): r
    for r in csv.DictReader(
        Path(os.environ.get("RK_PACK", os.path.join(HERE, "quests.csv"))).read_text(encoding="utf-8").splitlines()
    )
}


def turnins(events):
    out = []
    for e in events:
        if e.get("kind") == "turnin" and isinstance(e.get("q"), int) and e["q"] in PACK and e["q"] not in out:
            out.append(e["q"])
    return out


def zone_runs(qs):
    runs = []
    for q in qs:
        z = PACK[q]["end_zone"] or PACK[q]["zone"]
        if z in ("Darnassus",):
            z = "Teldrassil"  # same hub area for routing purposes
        if not runs or runs[-1] != z:
            runs.append(z)
    return runs


def lev(a, b):
    d = list(range(len(b) + 1))
    for i, x in enumerate(a, 1):
        prev, d[0] = d[0], i
        for j, y in enumerate(b, 1):
            cur = min(d[j] + 1, d[j - 1] + 1, prev + (x != y))
            prev, d[j] = d[j], cur
    return d[len(b)]


def kendall(order_a, order_b):
    common = [q for q in order_a if q in set(order_b)]
    if len(common) < 2:
        return 0.0
    pos_b = {q: i for i, q in enumerate(order_b)}
    conc = disc = 0
    for i in range(len(common)):
        for j in range(i + 1, len(common)):
            if pos_b[common[i]] < pos_b[common[j]]:
                conc += 1
            else:
                disc += 1
    return (conc - disc) / (conc + disc)


def binds(events):
    out = set()
    for e in events:
        if e.get("kind") == "home":
            t = (e.get("text") or e.get("place") or "").lower()
            for place in (
                "dolanaar",
                "auberdine",
                "lakeshire",
                "darnassus",
                "stormwind",
                "sentinel hill",
                "goldshire",
                "thelsamar",
                "menethil",
                "astranaar",
                "rut'theran",
                "ironforge",
            ):
                if place in t:
                    out.add(place)
    return out


def cut_at_level(plan, level=20.0):
    """Keep the plan's events up to the point the routekit sim reaches `level` (for 1-30 plans scored on 1-20)."""
    sys.path.insert(0, os.path.dirname(HERE))
    import rk

    lv = rk.simulate(plan, trace=True)["levels"]
    n = next((i for i, x in enumerate(lv) if x >= level), len(lv))
    # the hand-ins in the same town visit that crosses the level still belong to 1-20
    while n < len(plan["events"]) and plan["events"][n].get("kind") == "turnin":
        n += 1
    return {**plan, "events": plan["events"][:n]}


def score(plan, detail=False):
    if "--cut20" in sys.argv:
        plan = cut_at_level(plan)
    ref_t, gen_t = turnins(REF["events"]), turnins(plan["events"])
    common = set(ref_t) & set(gen_t)
    p = len(common) / len(gen_t) if gen_t else 0
    r = len(common) / len(ref_t)
    f1 = 2 * p * r / (p + r) if p + r else 0
    tau = kendall(ref_t, gen_t)
    order = (tau + 1) / 2 if common else 0
    zr, zg = zone_runs(ref_t), zone_runs(gen_t)
    zones = 1 - lev(zr, zg) / max(len(zr), len(zg), 1)
    br, bg = binds(REF["events"]), binds(plan["events"])
    hearth = len(br & bg) / len(br | bg) if br | bg else 1
    total = 100 * (0.45 * f1 + 0.25 * order + 0.20 * zones + 0.10 * hearth)
    res = {
        "total": round(total, 1),
        "selection_f1": round(f1, 3),
        "precision": round(p, 3),
        "recall": round(r, 3),
        "order": round(order, 3),
        "zones": round(zones, 3),
        "hearth": round(hearth, 3),
        "n_ref": len(ref_t),
        "n_gen": len(gen_t),
        "n_common": len(common),
    }
    if detail:
        res["ref_zone_runs"] = zr
        res["gen_zone_runs"] = zg
        res["ref_binds"], res["gen_binds"] = sorted(br), sorted(bg)
        res["missed"] = [(q, PACK[q]["name"], PACK[q]["zone"], PACK[q]["level"]) for q in ref_t if q not in common]
        res["extra"] = [(q, PACK[q]["name"], PACK[q]["zone"], PACK[q]["level"]) for q in gen_t if q not in common]
    return res


if __name__ == "__main__":
    plan = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    print(json.dumps(score(plan, "--detail" in sys.argv), indent=1, ensure_ascii=False))
