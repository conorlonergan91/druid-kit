"""routekit: tools for planning WoW Forever levelling routes (used by the planner agent and by Druid Kit updates).

Data: db.json (QuestieDB Forever + corrections + Questie user traces), travel.json (towns, boats, flights).
Everything here is maths and data; the decisions stay with the planner.

CLI (python3 rk.py <cmd> ...):
  quest ID...                         facts for quests: level, XP, giver/hand-in spots, objective spots, kills, prereqs
  available --level L [--done F]      quests a Night Elf Druid can take now (min level met, prereqs done), by zone
  hubs --level L [--done F] [--party N]   XP per hour for every hub at that arrival level (band -4..+1, plus +2/+3 in
                                       the current zone), with travel from --from TOWN
  loop --zone Z --quests ID... [--from TOWN] [--level L] [--party N] [--accepted ID,ID]
                                       best order of stops (accept, objectives, hand-in) by travel-salesman with
                                       precedence; prints stops, yards walked, minutes, XP
  sim PLAN.json                        replay a plan: levels, XP, minutes, prereq/min-level problems
  paths DruidKit.lua                   walked paths from the step log -> suggested via waypoints for routes
  calibrate DruidKit.lua               actual vs projected from the addon's step log: fight vs travel share
  cluster --quests ID... [--radius YD]  group quests whose objective areas are close; do each group in one visit
  party --level L --quests ID...      which kill quests save the most time in a group (kills shared, drops per player)
  itemplan STATE.json ROUTE.py         quest items needed much later: bank (bank on the way) or drop (starter that
                                       drops again) -> build/items.json
  vendors --zones "Z1,Z2"              Alliance vendors in those zones (bags-full prompt):
                                       [zone, x, y, name, what, repair]
  travel FROM TO [--flights "A;B"]     minutes and legs between two towns (boats with where to board, each
                                       flight hop, trams, roads); --flights = known flight-path towns
Done file: JSON list of quest IDs already handed in.
"""

import heapq
import importlib.util
import json
import math
import os
import re
import sys
from functools import cache, lru_cache
from pathlib import Path

HERE = os.path.dirname(os.path.abspath(__file__))
_DB = None


def db():
    global _DB
    if _DB is None:
        _DB = json.loads(Path(HERE, "db.json").read_text(encoding="utf-8"))
    return _DB


TRAVEL = json.loads(Path(HERE, "travel.json").read_text(encoding="utf-8"))

# Zone sizes in yards (classic maps, approximate) to turn map % into distance.
ZONE_YARDS = {k: tuple(v) for k, v in TRAVEL["zone_yards"].items()}
ZONE_IDS = {int(k): v for k, v in TRAVEL["zone_ids"].items()}
RUN_YPS = 7.0  # running speed, yards per second (no mount before 40)
PATH_FACTOR = 1.35  # real paths bend round hills, water and walls (step logs: ~1.3-1.5x a straight line)
NIGHTELF, DRUID = 8, 1024
XP_TO_LEVEL = [
    0,
    400,
    900,
    1400,
    2100,
    2800,
    3600,
    4500,
    5400,
    6500,
    7600,
    8800,
    10100,
    11400,
    12900,
    14400,
    16000,
    17700,
    19400,
    21300,
    23400,
    25700,
    28100,
    30500,
    33100,
    35400,
    38200,
    41000,
    43900,
    46800,
    49800,
]  # 25+ approx
QUEST_XP = {}


def _load_quest_xp():
    if QUEST_XP:
        return
    base = os.path.join(HERE, "data")
    for f in ("xpDB-classic.lua", "xpDB-traces.lua"):
        p = os.path.join(base, f)
        if os.path.exists(p):
            for m in re.finditer(r"\[(\d+)\]\s*=\s*\{(\d+),\s*(\d+)\}", Path(p).read_text(encoding="utf-8")):
                QUEST_XP[int(m.group(1))] = int(m.group(3))


# ---------------------------------------------------------------- places
_SUB = {}


def _subzones():
    if _SUB:
        return _SUB
    path = os.path.join(HERE, "data", "subZoneToParentZone.lua")
    if os.path.exists(path):
        for m in re.finditer(r"\[(\d+)\]\s*=\s*(\d+)", Path(path).read_text(encoding="utf-8")):
            _SUB.setdefault(int(m.group(1)), int(m.group(2)))
    _SUB.setdefault(0, 0)
    return _SUB


def zone_name(zid):
    zid = int(zid)
    if zid in ZONE_IDS:
        return ZONE_IDS[zid]
    parent = _subzones().get(zid)
    return ZONE_IDS.get(parent, str(zid)) if parent else str(zid)


def spawns(kind, oid):
    rec = db()["npcs" if kind == "npc" else "objects"].get(str(oid))
    if not rec or not rec.get("spawns"):
        return []
    out = []
    sp = rec["spawns"]
    if isinstance(sp, list):  # Lua arrays with a gap come through as lists
        sp = {i + 1: v for i, v in enumerate(sp) if v}
    for zid, pts in sp.items():
        z = zone_name(zid)
        for p in pts or []:
            if isinstance(p, list) and len(p) >= 2 and p[0] is not None and p[0] >= 0:
                out.append((z, float(p[0]), float(p[1])))
    return out


def yards(a, b):
    """Distance in yards between two (zone, x, y) points in the same zone, else None."""
    if a[0] != b[0] or a[0] not in ZONE_YARDS:
        return None
    w, h = ZONE_YARDS[a[0]]
    return math.hypot((a[1] - b[1]) / 100 * w, (a[2] - b[2]) / 100 * h)


def towns():
    return TRAVEL["towns"]


def _graph(flights=None):
    """Town graph. flights = set of known flight-path towns: flight edges need both ends known (None = all)."""
    g = {}
    for e in TRAVEL["edges"]:
        a, b, m = e["a"], e["b"], e["min"]
        if e.get("how") == "flight" and flights is not None and not (a in flights and b in flights):
            continue
        wait = (e.get("board") or {}).get("wait_min", 0)
        g.setdefault(a, []).append((b, m + wait, e))
        if not e.get("oneway"):
            g.setdefault(b, []).append((a, m + wait, e))
    return g


def travel_route(a, b, flights=None):
    """(minutes, legs) between two towns over walks, boats, flights, trams, portals; each leg says how and where to
    board. Every change of flight is its own leg, so "two flights" shows as two legs."""
    if a == b:
        return 0.0, []
    g = _graph(flights)
    dist, prev, pq = {a: 0.0}, {}, [(0.0, a)]
    while pq:
        d, u = heapq.heappop(pq)
        if u == b:
            legs, n = [], b
            while n != a:
                p, e = prev[n]
                leg = {"from": p, "to": n, "how": e.get("how") or e.get("note", "?"), "min": e["min"]}
                if e.get("board"):
                    leg["board"] = e["board"].get(p)
                    leg["wait_min"] = e["board"].get("wait_min")
                if e.get("note"):
                    leg["note"] = e["note"]
                legs.append(leg)
                n = p
            return d, legs[::-1]
        if d > dist.get(u, 1e9):
            continue
        for v, m, e in g.get(u, []):
            nd = d + m
            if nd < dist.get(v, 1e9):
                dist[v] = nd
                prev[v] = (u, e)
                heapq.heappush(pq, (nd, v))
    return float("inf"), []


def travel_min(a, b, flights=None):
    """Minutes between two towns (Dijkstra over walks, boats, flights, portals)."""
    return travel_route(a, b, flights)[0]


def nearest_town(p):
    best, bd = None, 1e18
    for name, t in towns().items():
        d = yards(p, (t["zone"], t["x"], t["y"]))
        if d is not None and d < bd:
            best, bd = name, d
    return best, bd


def move_min(a, b):
    """Minutes from point a to point b: run inside a zone, else run to a town, travel, run on."""
    d = yards(a, b)
    if d is not None:
        return d * PATH_FACTOR / RUN_YPS / 60
    ta, da = nearest_town(a)
    tb, db_ = nearest_town(b)
    if ta is None or tb is None:
        return 15.0
    return (da + db_) * PATH_FACTOR / RUN_YPS / 60 + travel_min(ta, tb)


# ---------------------------------------------------------------- quests
def _ids(field):
    """startedBy/finishedBy -> (npcs, objects, items) lists, whatever shape the DB used."""
    out = ([], [], [])
    if not field:
        return out
    if isinstance(field, dict):
        for k, v in field.items():
            if v and 1 <= int(k) <= 3:
                out[int(k) - 1].extend(v)
        return out
    for i, v in enumerate(field[:3]):
        if v:
            out[i].extend(v)
    return out


def _objectives(q):
    obj = q.get("objectives")
    res = {"creatures": [], "objects": [], "items": []}
    if not obj:
        return res
    parts = {int(k): v for k, v in obj.items()} if isinstance(obj, dict) else dict(enumerate(obj, 1))
    for idx, key in ((1, "creatures"), (2, "objects"), (3, "items")):
        for e in parts.get(idx) or []:
            if e and e[0]:
                res[key].append(e[0])
    return res


def _count_from_text(q):
    nums = [int(n) for n in re.findall(r"\b(\d{1,2})\b", " ".join(q.get("objectivesText") or []))]
    return max(nums) if nums else 0


@lru_cache(maxsize=1)
def _classic_ids():
    p = os.path.join(HERE, "data", "classic_quest_ids.json")
    return set(json.loads(Path(p).read_text(encoding="utf-8"))) if os.path.exists(p) else set()


@cache
def quest(qid):
    _load_quest_xp()
    q = db()["quests"].get(str(qid))
    if not q:
        return None
    sn, so, si = _ids(q.get("startedBy"))
    fn, fo, _ = _ids(q.get("finishedBy"))
    start = [p for n in sn for p in spawns("npc", n)[:1]] + [p for o in so for p in spawns("object", o)[:1]]
    end = [p for n in fn for p in spawns("npc", n)[:1]] + [p for o in fo for p in spawns("object", o)[:1]]
    objs = _objectives(q)
    targets, mob_levels = [], []
    for c in objs["creatures"]:
        targets.extend(spawns("npc", c))
        n = db()["npcs"].get(str(c))
        if n and n.get("minLevel"):
            mob_levels.append((n["minLevel"] + n.get("maxLevel", n["minLevel"])) / 2)
    for o in objs["objects"]:
        targets.extend(spawns("object", o))
    drops = 0
    for it in objs["items"]:
        irec = db()["items"].get(str(it)) or {}
        for n in irec.get("npcDrops") or []:
            sp = spawns("npc", n)
            targets.extend(sp)
            nr = db()["npcs"].get(str(n))
            if nr and nr.get("minLevel"):
                mob_levels.append((nr["minLevel"] + nr.get("maxLevel", nr["minLevel"])) / 2)
            drops += 1
        for o in irec.get("objectDrops") or []:
            targets.extend(spawns("object", o))
    te = q.get("triggerEnd")
    if isinstance(te, list) and len(te) > 1 and isinstance(te[1], dict):
        for zid, pts in te[1].items():  # explore objectives: reach a spot
            targets.extend((zone_name(zid), float(p[0]), float(p[1])) for p in pts or [] if p and p[0] is not None)
    count = _count_from_text(q)
    kills = 0
    if objs["creatures"]:
        kills += count or 8
    if drops:
        kills += int((count or 6) / 0.45)  # quest drops ~45% of the time
    elite = any((db()["npcs"].get(str(c)) or {}).get("rank", 0) in (1, 2, 3) for c in objs["creatures"])
    pre_all = q.get("preQuestGroup") or []
    pre_any = q.get("preQuestSingle") or []
    return {
        "id": int(qid),
        "name": q.get("name"),
        "level": q.get("questLevel") or 0,
        "min": q.get("requiredLevel") or 1,
        "races": q.get("requiredRaces") or 0,
        "classes": q.get("requiredClasses") or 0,
        "zone": zone_name(q.get("zoneOrSort")) if (q.get("zoneOrSort") or 0) > 0 else "class/other",
        "start": start[:1],
        "start_item": bool(si),
        "end": end[:1],
        "targets": targets,
        "target_center": _center([t for t in targets if start and t[0] == start[0][0]])
        or _center([t for t in targets if t[0] in ZONE_YARDS])
        or _center(targets)
        or (start[0] if (objs["creatures"] or objs["items"] or objs["objects"]) and start else None),
        "spot_known": bool([t for t in targets if t[0] in ZONE_YARDS]),
        "kills": kills,
        "mob_level": (sum(mob_levels) / len(mob_levels)) if mob_levels else None,
        "elite": elite,
        "xp": QUEST_XP.get(int(qid), 0),
        "pre_all": pre_all,
        "pre_any": pre_any,
        "exclusive": q.get("exclusiveTo") or [],
        "next": q.get("nextQuestInChain"),
        "text": " ".join(q.get("objectivesText") or [])[:160],
        "repeatable": bool((q.get("specialFlags") or 0) & 1),
        "forever_new": int(qid) not in _classic_ids(),  # not in Questie's Classic Era DB: new or reworked in Forever
    }


def _center(pts):
    """Densest spot among the targets (zone with most spawns, then its median point)."""
    if not pts:
        return None
    by = {}
    for p in pts:
        by.setdefault(p[0], []).append(p)
    z, ps = max(by.items(), key=lambda kv: len(kv[1]))
    xs, ys = sorted(p[1] for p in ps), sorted(p[2] for p in ps)
    return (z, xs[len(xs) // 2], ys[len(ys) // 2])


def eligible(q):
    if q is None or q["repeatable"]:
        return False
    if q["races"] and not (int(q["races"]) & NIGHTELF):
        return False
    return not (q["classes"] and not (int(q["classes"]) & DRUID))


def prereqs_ok(q, done):
    if q["pre_all"] and not all(p in done for p in q["pre_all"]):
        return False
    if q["pre_any"] and not any(p in done for p in q["pre_any"]):
        return False
    return not (q["exclusive"] and any(p in done for p in q["exclusive"]))


# ---------------------------------------------------------------- XP and time
def quest_xp(q, level):
    xp = q["xp"] or 0
    diff = level - q["level"]
    if diff >= 10:
        return int(xp * 0.1)
    if diff >= 6:
        return int(xp * (1 - 0.2 * (diff - 5)))
    return xp


def mob_xp(mob_level, level):
    """Classic kill XP for a normal mob."""
    base = level * 5 + 45
    diff = mob_level - level
    if diff >= 0:
        return base * (1 + 0.05 * min(diff, 4))
    zd = (
        5
        if level < 8
        else (6 if level < 10 else (7 if level < 12 else (8 if level < 16 else (9 if level < 20 else 11))))
    )
    if -diff >= zd + 1:  # grey
        return 0
    return base * (1 - (-diff) / zd)


def sec_per_kill(mob_level, level, party=1):
    """Fight plus a share of downtime, by level difference."""
    diff = (mob_level or level) - level
    base = 22 + 6 * diff if diff >= 0 else max(12, 22 + 3 * diff)
    return base * 1.3 / max(1, party**0.85)


GRIND_FACTOR = 1.8  # pure grinding: finding spawns, eating, competition — slower than kills done while questing


def grind_xp_per_min(level):
    return mob_xp(level, level) * 60 / (sec_per_kill(level, level) * GRIND_FACTOR)


def quest_minutes(q, level, party=1, from_point=None):
    """Minutes to do a quest's objectives once you're at its area (no hub travel)."""
    lvl = q["mob_level"] or q["level"]
    kills = q["kills"]
    if q["elite"]:
        kills = max(kills, 3)
    m = kills * sec_per_kill(lvl, level, party) / 60
    if q["targets"] and not q["kills"]:
        m += 2.0  # click objects
    if not q.get("spot_known", True):
        m += 6.0  # place not in the data: allow time to find it
    if q["elite"] and party == 1:
        m *= 2.5  # solo elites: slow and risky
    return m + 1.0  # talk to giver and hand in


def kill_xp(q, level, party=1):
    lvl = q["mob_level"] or q["level"]
    return q["kills"] * mob_xp(lvl, level) / max(1, party)


def level_of(total_xp):
    lvl, acc = 1, 0
    while lvl < len(XP_TO_LEVEL) and acc + XP_TO_LEVEL[lvl] <= total_xp:
        acc += XP_TO_LEVEL[lvl]
        lvl += 1
    return lvl + (total_xp - acc) / XP_TO_LEVEL[lvl] if lvl < len(XP_TO_LEVEL) else lvl


def xp_at(level):
    whole = int(level)
    return sum(XP_TO_LEVEL[1:whole]) + (level - whole) * XP_TO_LEVEL[whole]


# ---------------------------------------------------------------- route order (travel salesman with precedence)
def order_stops(stops, start):
    """stops: list of dicts {key, point, after:[keys]}. Nearest-neighbour then 2-opt, keeping precedence."""

    def cost(seq):
        c, cur = 0.0, start
        for s in seq:
            c += move_min(cur, s["point"]) if cur else 0
            cur = s["point"]
        return c

    def valid(seq):
        seen = set()
        for s in seq:
            if any(a not in seen for a in s.get("after", [])):
                return False
            seen.add(s["key"])
        return True

    left, seq, cur = list(stops), [], start
    keys = {s["key"] for s in stops}
    while left:
        ready = [s for s in left if all(a in {x["key"] for x in seq} or a not in keys for a in s.get("after", []))]
        if not ready:
            ready = left
        nxt = min(ready, key=lambda s: move_min(cur, s["point"]) if cur else 0)
        seq.append(nxt)
        left.remove(nxt)
        cur = nxt["point"]
    best, bc = seq, cost(seq)
    improved = True
    while improved and len(best) < 120:
        improved = False
        for i in range(len(best) - 1):
            for j in range(i + 2, len(best) + 1):
                cand = best[:i] + best[i:j][::-1] + best[j:]
                if valid(cand):
                    c = cost(cand)
                    if c < bc - 1e-6:
                        best, bc, improved = cand, c, True
    return best, bc


def loop_plan(qids, start_point, level, party=1, accepted=()):
    """Order accept / objective / hand-in stops for these quests and estimate time and XP."""
    stops = []
    for qid in qids:
        q = quest(qid)
        if not q:
            continue
        k = str(qid)
        if qid not in accepted and q["start"]:
            stops.append(
                {"key": "a" + k, "point": q["start"][0], "label": f"accept {q['name']}", "q": qid, "kind": "accept"}
            )
        after = ["a" + k] if qid not in accepted and q["start"] else []
        if q["target_center"]:
            stops.append(
                {
                    "key": "o" + k,
                    "point": q["target_center"],
                    "after": after,
                    "label": f"do {q['name']}",
                    "q": qid,
                    "kind": "complete",
                }
            )
            after = ["o" + k]
        if q["end"]:
            stops.append(
                {
                    "key": "t" + k,
                    "point": q["end"][0],
                    "after": after,
                    "label": f"hand in {q['name']}",
                    "q": qid,
                    "kind": "turnin",
                }
            )
    seq, travel = order_stops(stops, start_point)
    lvl, work, xp = level, 0.0, 0.0
    total = xp_at(level)
    for s in seq:
        q = quest(s["q"])
        if s["kind"] == "complete":
            work += quest_minutes(q, lvl, party)
            xp += kill_xp(q, lvl, party)
        elif s["kind"] == "turnin":
            xp += quest_xp(q, lvl)
        lvl = level_of(total + xp)
    return {
        "stops": seq,
        "travel_min": round(travel, 1),
        "work_min": round(work, 1),
        "xp": int(xp),
        "end_level": round(lvl, 2),
        "xp_per_hour": int(xp / max(1e-6, (travel + work) / 60)),
    }


# ---------------------------------------------------------------- hubs
def available(level, done, zones=None, window=(4, 1)):
    out = []
    for k in db()["quests"]:
        q = quest(int(k))
        if not eligible(q) or int(k) in done:
            continue
        if q["min"] > level + 0.01 or not prereqs_ok(q, done):
            continue
        if not (level - window[0] <= q["level"] <= level + window[1]):
            continue
        z = q["start"][0][0] if q["start"] else q["zone"]
        if zones and z not in zones:
            continue
        out.append(q)
    return out


def hubs(level, done, from_town=None, party=1, current_zone=None):
    rows = []
    for hub, info in TRAVEL["hubs"].items():
        town = info["town"]
        t = towns()[town]
        # Once you're in a hub you grow into its higher quests, so judge every hub over the same -4..+3 band;
        # the loop's time model already charges more for quests above you.
        win = (4, 3)
        zs = set(info["zones"])
        qs = [q for q in available(level, done, zones=zs, window=win) if q["start"]]
        # breadcrumbs/deliveries picked up elsewhere (capitals, current hub) that end in this hub
        qs += [
            q
            for q in available(level, done, window=win)
            if q["start"]
            and q["end"]
            and q["end"][0][0] in zs
            and q["start"][0][0] not in zs
            and q["start"][0][0] in (current_zone, "Stormwind City", "Darnassus", "Ironforge")
        ]
        qs = [q for q in qs if q["end"]]
        if len(qs) < 3:
            opens = next(
                (
                    lv
                    for lv in range(int(level) + 1, int(level) + 8)
                    if len(
                        [
                            q
                            for q in available(lv, done, zones=set(info["zones"]), window=(4, 1))
                            if q["start"] and q["end"]
                        ]
                    )
                    >= 5
                ),
                None,
            )
            rows.append({"hub": hub, "quests": len(qs), "xp_per_hour": 0, "opens_at_level": opens})
            continue
        plan = loop_plan([q["id"] for q in qs], (t["zone"], t["x"], t["y"]), level, party)
        trip = travel_min(from_town, town) if from_town else 0
        hours = (plan["travel_min"] + plan["work_min"] + trip) / 60
        rows.append(
            {
                "hub": hub,
                "quests": len(qs),
                "xp": plan["xp"],
                "trip_min": round(trip, 1),
                "loop_min": round(plan["travel_min"] + plan["work_min"], 1),
                "xp_per_hour": int(plan["xp"] / max(hours, 1e-6)),
                "end_level": plan["end_level"],
            }
        )
    rows.append({"hub": "(grind at your level)", "xp_per_hour": int(grind_xp_per_min(level) * 60)})
    return sorted(rows, key=lambda r: -r["xp_per_hour"])


def party_savings(qids, level):
    out = []
    for qid in qids:
        q = quest(qid)
        if not q or not q["kills"]:
            continue
        solo = quest_minutes(q, level, 1)
        duo = quest_minutes(q, level, 2)
        lost = kill_xp(q, level, 1) - kill_xp(q, level, 2)  # mob XP is split in a party
        solo_rate = (q["xp"] + kill_xp(q, level, 1)) / solo * 60
        duo_rate = (q["xp"] + kill_xp(q, level, 2)) / duo * 60
        out.append(
            {
                "q": qid,
                "name": q["name"],
                "kills": q["kills"],
                "elite": q["elite"],
                "solo_min": round(solo, 1),
                "group_min": round(duo, 1),
                "saved_min": round(solo - duo, 1),
                "mob_xp_lost": int(lost),
                "xp_per_hour_solo": int(solo_rate),
                "xp_per_hour_group": int(duo_rate),
                "group_worth_it": duo_rate > solo_rate * 1.1 or q["elite"],
            }
        )
    return sorted(out, key=lambda r: -(r["xp_per_hour_group"] - r["xp_per_hour_solo"]))


def calibrate(saved_vars):
    """Actual vs projected from the addon's step log (DruidKit SavedVariables): fight vs travel time, est ratio."""
    from lupa.lua51 import LuaRuntime

    lua = LuaRuntime()
    lua.execute(Path(saved_vars).read_text(encoding="utf-8"))
    db_ = lua.globals().DruidKitDB
    log = [db_.stepLog[i] for i in range(1, len(db_.stepLog) + 1)] if db_ and db_.stepLog else []
    kinds, ratios = {}, []
    for e in log:
        kind = "fight" if e["do"] == "complete" else "travel/talk"
        k = kinds.setdefault(kind, {"secs": 0, "xp": 0, "steps": 0})
        k["secs"] += e.secs or 0
        k["xp"] += e.xp or 0
        k["steps"] += 1
        if e.est and e.secs:
            ratios.append(e.secs / (e.est * 60))
    total = sum(k["secs"] for k in kinds.values()) or 1
    for k in kinds.values():
        k["share"] = round(k["secs"] / total, 2)
        k["minutes"] = round(k["secs"] / 60, 1)
    return {
        "kinds": kinds,
        "xp_per_hour": int(sum(k["xp"] for k in kinds.values()) * 3600 / total),
        "actual_over_est": round(sum(ratios) / len(ratios), 2) if ratios else None,
        "steps": len(log),
    }


def _simplify(pts, eps):
    """Douglas-Peucker on (x, y) map points: keep the corners of a walked path, drop the straight bits."""
    if len(pts) < 3:
        return pts
    (ax, ay), (bx, by) = pts[0], pts[-1]
    dx, dy = bx - ax, by - ay
    norm = (dx * dx + dy * dy) ** 0.5 or 1e-9
    far, idx = 0.0, 0
    for i, (x, y) in enumerate(pts[1:-1], 1):
        d = abs(dy * (x - ax) - dx * (y - ay)) / norm
        if d > far:
            far, idx = d, i
    if far <= eps:
        return [pts[0], pts[-1]]
    return _simplify(pts[: idx + 1], eps)[:-1] + _simplify(pts[idx:], eps)


def learned_paths(saved_vars, eps=0.012):
    """Walked paths from the addon's step log -> suggested `via` waypoints and how much longer than a straight
    line the real path was. Only steps where the walk bent noticeably are suggested."""
    from lupa.lua51 import LuaRuntime

    lua = LuaRuntime()
    lua.execute(Path(saved_vars).read_text(encoding="utf-8"))
    db_ = lua.globals().DruidKitDB
    out = []
    for i in range(1, len(db_.stepLog) + 1 if db_ and db_.stepLog else 1):
        e = db_.stepLog[i]
        if not e.trail:
            continue
        pts = [p.split(":") for p in e.trail.split(";")]
        mid = int(pts[-1][0])
        xy = [tuple(float(v) for v in p[1].split(",")) for p in pts if int(p[0]) == mid]
        if len(xy) < 3:
            continue
        walked = sum(
            ((xy[k][0] - xy[k - 1][0]) ** 2 + (xy[k][1] - xy[k - 1][1]) ** 2) ** 0.5 for k in range(1, len(xy))
        )
        straight = ((xy[-1][0] - xy[0][0]) ** 2 + (xy[-1][1] - xy[0][1]) ** 2) ** 0.5
        ratio = walked / straight if straight > 0.01 else None
        corners = _simplify(xy, eps)[1:-1]
        if ratio and ratio > 1.25 and corners:
            out.append(
                {
                    "step": e.i,
                    "q": e.q,
                    "name": e.name,
                    "target": e.target,
                    "path_factor": round(ratio, 2),
                    "via": [[mid, round(x * 100, 1), round(y * 100, 1)] for x, y in corners[:6]],
                }
            )
    return out


def clusters(qids, radius=400):
    """Group quests whose objective areas lie within `radius` yards (single-link). Do each group in one visit."""
    pts = []
    for qid in qids:
        q = quest(qid)
        if q and q["target_center"]:
            pts.append((qid, q["name"], q["target_center"]))
    parent = list(range(len(pts)))

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    for i in range(len(pts)):
        for j in range(i + 1, len(pts)):
            d = yards(pts[i][2], pts[j][2])
            if d is not None and d <= radius:
                parent[find(i)] = find(j)
    groups = {}
    for i, p in enumerate(pts):
        groups.setdefault(find(i), []).append(p)
    out = []
    for g in groups.values():
        c = _center([p[2] for p in g])
        out.append({"center": [c[0], round(c[1], 1), round(c[2], 1)], "quests": [[p[0], p[1]] for p in g]})
    return sorted(out, key=lambda r: -len(r["quests"]))


# ---------------------------------------------------------------- plan replay
# ---------------------------------------------------------------- character power
TRAINER_TOWNS = ("Shadowglen", "Dolanaar", "Darnassus", "Nighthaven", "Stormwind")  # druid trainers
FORM_QUESTS = {6001: ("Bear Form", 0.88), 5061: ("Aquatic Form", 0.97), 98397: ("Cat Form", 0.92)}
RANK_PENALTY = 0.05  # each trainer level (even levels from 4) you haven't trained: ~5% slower kills
PENALTY_CAP = 0.35


def missed_ranks(level, trained):
    return sum(1 for lv in range(4, int(level) + 1, 2) if lv > trained)


def rank_factor(level, trained):
    return 1 + min(PENALTY_CAP, RANK_PENALTY * missed_ranks(level, trained))


def power_factor(level, trained, forms):
    """Multiplier on fight time: untrained ranks make you slower, class-quest forms make you faster."""
    f = 1 + min(PENALTY_CAP, RANK_PENALTY * missed_ranks(level, trained))
    for qid in forms:
        f *= FORM_QUESTS[qid][1]
    return f


def train_trip(cur, level):
    """Cheapest trainer from where you stand: (minutes there, town). Teleport: Moonglade from 10."""
    here, _ = nearest_town(cur) if cur else (None, 0)
    best = (1e9, None)
    for t in TRAINER_TOWNS:
        if t == "Nighthaven" and level < 10:
            continue
        m = 0.0 if here == t else (travel_min(here, t) if here else 0.0)
        if t == "Nighthaven" and level >= 10:
            m = min(m, 0.5)  # Teleport: Moonglade (10s cast + load)
        best = min(best, (m, t))
    return best


def _town_in(text):
    """The town named in a piece of text (longest name first, so 'Stormwind' doesn't eat 'Stormwind City')."""
    t = (text or "").lower()
    for n in sorted(towns(), key=len, reverse=True):
        if n.lower() in t:
            return n
    return None


def _town_at(p, radius=300):
    """The town whose centre is within `radius` yards of point p, if any."""
    if not p:
        return None
    n, d = nearest_town(p)
    return n if d is not None and d <= radius else None


def simulate(plan, trace=False):
    mins = []
    start = plan.get("start") or {}
    levels, trained, forms, visits, penalty_min, rank_lag = [], 1, set(), 0, 0.0, []
    home = _town_in(start.get("home")) if start.get("home") else None
    known = {n for n in (_town_in(f) for f in start.get("flights", [])) if n}
    known |= {n for n, v in towns().items() if v.get("always_known")}
    visited_fm, learned, last_hearth = {}, [], None
    cd = TRAVEL.get("hearth_cooldown_min", 60)
    done, accepted = set(start.get("done", [])), set(start.get("accepted", []))
    total, minutes, problems, cur = 0.0, 0.0, [], None
    if start.get("level"):
        total = xp_at(float(start["level"]))
    if start.get("at"):
        t = towns().get(_town_in(start["at"]) or "")
        cur = (t["zone"], t["x"], t["y"]) if t else None
    for i, e in enumerate(plan["events"]):
        here = _town_at(cur)
        if here and towns()[here].get("fm") and here not in known:
            visited_fm.setdefault(here, i)
        k, qid = e.get("kind"), e.get("q")
        lvl = level_of(total)
        levels.append(round(lvl, 2))
        mins.append(minutes)
        q = quest(qid) if qid else None
        if k == "accept" and q:
            if q["min"] > lvl + 0.01:
                problems.append(f"#{i} accept {qid} {q['name']} needs {q['min']}, you are {lvl:.1f}")
            if not prereqs_ok(q, done):
                problems.append(f"#{i} accept {qid} {q['name']} before its prerequisites")
            accepted.add(qid)
            if q["start"]:
                minutes += move_min(cur, q["start"][0]) if cur else 0
                cur = q["start"][0]
        elif k == "turnin" and q:
            if qid not in accepted and q["start"]:
                problems.append(f"#{i} hand in {qid} {q['name']} without accepting")
            if q["target_center"]:
                pf = power_factor(lvl, trained, forms)
                qm = quest_minutes(q, lvl)
                minutes += (move_min(cur, q["target_center"]) if cur else 0) + qm * pf
                penalty_min += qm * pf * (1 - 1 / rank_factor(lvl, trained))
                cur = q["target_center"]
                total += kill_xp(q, lvl)
            if q["end"]:
                minutes += move_min(cur, q["end"][0]) if cur else 0
                cur = q["end"][0]
            total += quest_xp(q, lvl)
            done.add(qid)
            if qid in FORM_QUESTS:
                forms.add(qid)
        elif k == "grind":
            target = float(e.get("to", lvl))
            need = max(0.0, xp_at(target) - total)
            pf = power_factor(lvl, trained, forms)
            minutes += need / grind_xp_per_min(lvl) * pf
            penalty_min += need / grind_xp_per_min(lvl) * pf * (1 - 1 / rank_factor(lvl, trained))
            total += need
        elif k == "train":
            m, town = train_trip(cur, lvl)
            if cur and m > 0.6:
                t = towns()[town]
                minutes += m
                cur = (t["zone"], t["x"], t["y"])
            minutes += 1.0
            visits += 1
            rank_lag.append(missed_ranks(lvl, trained))
            trained = int(lvl)
        elif k == "home":
            town = _town_in(e.get("at") or e.get("text"))
            if town and cur and _town_at(cur) not in (None, town):
                problems.append(f"#{i} set hearth to {town} while you are in {_town_at(cur)}: go there first")
            home = town or home
        elif k == "fp":
            town = _town_in(e.get("at") or e.get("text"))
            if town and not towns()[town].get("fm"):
                problems.append(f"#{i} {town} has no flight master in the travel data")
            if town and town not in known:
                known.add(town)
                learned.append(town)
                t = towns()[town]
                minutes += (move_min(cur, (t["zone"], t["x"], t["y"])) if cur else 0) + 0.5
                cur = (t["zone"], t["x"], t["y"])
        elif k == "travel":
            txt = (e.get("text") or "").lower()
            if "fly" in txt or "flight" in txt:
                dest = _town_in(txt.split(" to ", 1)[1] if " to " in txt else txt)
                if dest and towns()[dest].get("fm") and dest not in known:
                    problems.append(
                        f"#{i} flight to {dest} before its flight path is learned (add an fp event "
                        "when you first walk there, or walk/boat instead)"
                    )
        elif k == "hearth":
            minutes += 0.3
            if not home:
                problems.append(f"#{i} hearth with no hearthstone set: add a home event in the town you'll return to")
            elif _town_in(e.get("text")) not in (None, home):
                problems.append(f"#{i} hearth to {_town_in(e.get('text'))}, but the hearthstone is set to {home}")
            if last_hearth is not None and minutes - last_hearth < cd:
                problems.append(f"#{i} hearth on cooldown ({minutes - last_hearth:.0f} of {cd} min since the last one)")
            last_hearth = minutes
            if home:
                t = towns()[home]
                cur = (t["zone"], t["x"], t["y"])
    out = {
        "final_level": round(level_of(total), 2),
        "hours": round(minutes / 60, 1),
        "quests": len(done),
        "trainer_visits": visits,
        "untrained_ranks_now": missed_ranks(level_of(total), trained),
        "slowdown_from_missed_training_min": round(penalty_min, 1),
        "forms": [FORM_QUESTS[q][0] for q in sorted(forms)],
        "flight_paths_learned": learned,
        "home_at_end": home,
        "problems": (
            problems
            + [
                f"#{i} walked through {t} (flight master) without learning its flight path: add an fp event there"
                for t, i in visited_fm.items()
                if t not in known
            ]
        )[:30],
    }
    reach = next((m for lv_, m in zip(levels, mins, strict=True) if lv_ >= 20), None)
    out["hours_to_20"] = round(reach / 60, 1) if reach is not None else None
    if trace:
        out["levels"] = levels
    return out


BANK_ZONES = {"Stormwind City", "Ironforge", "Darnassus"}


def item_plan(state, route, soon=20, bank_within=30):
    """Quest items in the bags that the route won't need for a while: bank them if a bank is on the way, or drop a
    quest-start item that drops again (when its quest isn't in the route). -> {item name: {action, why}}."""
    d = db()
    log = {int(k) for k in state.get("log", {})}
    done = set(state.get("done", []))
    flat = [st for sec in route["sections"] for st in sec["steps"]]
    by_item = {}
    for qid, q in d["quests"].items():
        src = q.get("sourceItemId")
        if src:
            by_item.setdefault(int(src), set()).add(int(qid))
        for group in (q.get("objectives") or {}).values() if isinstance(q.get("objectives"), dict) else []:
            for o in group or []:
                if isinstance(o, list) and o and isinstance(o[0], int):
                    by_item.setdefault(o[0], set()).add(int(qid))
    bank = next(
        (
            (i, st["goto"][0])
            for i, st in enumerate(flat[:bank_within])
            if st.get("goto") and st["goto"][0] in BANK_ZONES
        ),
        None,
    )
    out = {}
    for name, inv in (state.get("inventory") or {}).items():
        iid = inv.get("id")
        item = d["items"].get(str(iid)) or {}
        quests = set(by_item.get(iid, set())) | set(item.get("relatedQuests") or [])
        start = item.get("startQuest")
        if start:
            quests.add(int(start))
        live = sorted(q for q in quests if q in log or (q == start and q not in done))
        if not live:
            continue
        q = live[0]
        title = (d["quests"].get(str(q)) or {}).get("name", f"quest {q}")
        ahead = next((i for i, st in enumerate(flat) if st.get("q") == q), None)
        if ahead is not None:
            continue  # the route does this quest: keep it in the bags
        when = f"about {ahead} steps away" if ahead is not None else "not in your current route"
        # Only bank what the current route won't ask for: a bank is passed before the quest comes up again.
        can_bank = bank and ahead is None
        sources = [((d["objects"].get(str(o)) or {}).get("name") or "") for o in item.get("objectDrops") or []]
        sources += [((d["npcs"].get(str(n)) or {}).get("name") or "") for n in item.get("npcDrops") or []]
        sources = [x for x in dict.fromkeys(sources) if x][:2]
        if start == q and q not in log and sources and ahead is None:
            from_ = " and ".join(sources)
            out[name] = {"action": "drop", "why": f"starts {title} ({when}); it drops again from {from_}"}
        elif can_bank:
            out[name] = {
                "action": "bank",
                "why": f"needed later for {title} ({when}); bank it in {bank[1]} (in about {bank[0]} steps)",
            }
    return out


VENDOR_FLAG, REPAIR_FLAG = 4, 16384  # QuestieDB npcFlags (classic layout)


def vendors(zones):
    """Alliance-friendly vendors in the zones: [zone, x, y, name, what, repair]. For the bags-full prompt."""
    want = set(zones)
    out = []
    for rec in db()["npcs"].values():
        flags = rec.get("npcFlags") or 0
        if not flags & VENDOR_FLAG or "A" not in (rec.get("friendlyToFaction") or ""):
            continue
        sp = rec.get("spawns") or {}
        if isinstance(sp, list):
            sp = {i + 1: v for i, v in enumerate(sp) if v}
        for zid, pts in sp.items():
            z = zone_name(zid)
            if z not in want:
                continue
            for p in pts or []:
                if isinstance(p, list) and len(p) >= 2 and p[0] is not None and p[0] >= 0:
                    out.append(
                        [
                            z,
                            round(float(p[0]), 1),
                            round(float(p[1]), 1),
                            rec.get("name"),
                            rec.get("subName") or "",
                            bool(flags & REPAIR_FLAG),
                        ]
                    )
                    break
    return sorted(out)


# ---------------------------------------------------------------- CLI
def _done(args):
    if "--done" in args:
        return set(json.loads(Path(args[args.index("--done") + 1]).read_text(encoding="utf-8")))
    return set()


def _opt(args, name, default=None, cast=str):
    return cast(args[args.index(name) + 1]) if name in args else default


def main(argv):
    if not argv:
        print(__doc__)
        return
    cmd, args = argv[0], argv[1:]
    if cmd == "quest":
        for a in args:
            q = quest(int(a))
            print(
                json.dumps(
                    {k: v for k, v in q.items() if k != "targets"} | {"n_targets": len(q["targets"])},
                    ensure_ascii=False,
                )
                if q
                else f"{a}: unknown"
            )
    elif cmd == "available":
        lvl = _opt(args, "--level", 1, float)
        rows = available(lvl, _done(args), window=(_opt(args, "--below", 4, int), _opt(args, "--above", 1, int)))
        by = {}
        for q in rows:
            if eligible(q):
                z = q["start"][0][0] if q["start"] else q["zone"]
                by.setdefault(z, []).append(f"{q['id']} {q['name']} (L{q['level']}, {q['xp']}xp)")
        for z, qs in sorted(by.items(), key=lambda kv: -len(kv[1])):
            print(f"{z}: {len(qs)}")
            for s in qs:
                print("   ", s)
    elif cmd == "hubs":
        for r in hubs(
            _opt(args, "--level", 1, float),
            _done(args),
            _opt(args, "--from"),
            _opt(args, "--party", 1, int),
            _opt(args, "--current"),
        ):
            print(json.dumps(r))
    elif cmd == "loop":
        qids = [int(x) for x in args[args.index("--quests") + 1 :] if x.isdigit()]
        town = _opt(args, "--from")
        start = None
        if town:
            t = towns()[town]
            start = (t["zone"], t["x"], t["y"])
        acc = {int(x) for x in (_opt(args, "--accepted", "") or "").split(",") if x.strip().isdigit()}
        res = loop_plan(qids, start, _opt(args, "--level", 10, float), _opt(args, "--party", 1, int), accepted=acc)
        for s in res["stops"]:
            p = s["point"]
            print(f"{s['kind']:8} {s['q']:>6}  {p[0]} ({p[1]:.1f}, {p[2]:.1f})  {s['label']}")
        print(json.dumps({k: v for k, v in res.items() if k != "stops"}))
    elif cmd == "sim":
        print(json.dumps(simulate(json.loads(Path(args[0]).read_text(encoding="utf-8"))), indent=1))
    elif cmd == "paths":
        for r in learned_paths(args[0]):
            print(json.dumps(r, ensure_ascii=False))
    elif cmd == "calibrate":
        print(json.dumps(calibrate(args[0]), indent=1))
    elif cmd == "cluster":
        i = args.index("--quests") + 1
        qids = []
        while i < len(args) and args[i].isdigit():
            qids.append(int(args[i]))
            i += 1
        for r in clusters(qids, _opt(args, "--radius", 400, float)):
            print(json.dumps(r, ensure_ascii=False))
    elif cmd == "party":
        qids = [int(x) for x in args[args.index("--quests") + 1 :] if x.isdigit()]
        for r in party_savings(qids, _opt(args, "--level", 10, float)):
            print(json.dumps(r, ensure_ascii=False))
    elif cmd == "itemplan":
        state = json.loads(Path(args[0]).read_text(encoding="utf-8"))
        spec = importlib.util.spec_from_file_location("route", args[1])
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        print(json.dumps(item_plan(state, mod.ROUTE), ensure_ascii=False, indent=1))
    elif cmd == "vendors":
        print(
            json.dumps(
                vendors([z.strip() for z in _opt(args, "--zones", "").split(",") if z.strip()]), ensure_ascii=False
            )
        )
    elif cmd == "travel":
        known = _opt(args, "--flights")
        m, legs = travel_route(args[0], args[1], set(known.split(";")) if known else None)
        print(json.dumps({"min": m, "legs": legs}, ensure_ascii=False, indent=1))
    else:
        print(__doc__)


if __name__ == "__main__":
    main(sys.argv[1:])
