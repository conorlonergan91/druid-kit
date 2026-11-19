"""Route planner maths (planner/rk.py) without the quest database: travel, training model, clustering."""

import sys
import tempfile
from pathlib import Path

from expect import check, done
from wowenv import ROOT

sys.path.insert(0, str(ROOT / "planner"))
import rk  # noqa: E402

check(rk.travel_min("Auberdine", "Auberdine") == 0, "same town costs nothing", "")
t = rk.travel_min("Dolanaar", "Lakeshire")
check(t is not None and 10 < t < 60, "Dolanaar to Lakeshire goes by boat and road", t)
check(rk.travel_min("Stormwind", "Nighthaven") >= 0, "Nighthaven reachable", "")

check(rk.missed_ranks(10, 10) == 0, "trained at 10: nothing missed", "")
check(rk.missed_ranks(14, 9) == 3, "trained at 9, now 14: ranks at 10, 12, 14 missed", rk.missed_ranks(14, 9))
check(abs(rk.rank_factor(14, 9) - 1.15) < 1e-9, "3 missed ranks = 15% slower fights", rk.rank_factor(14, 9))
check(rk.rank_factor(30, 1) == 1 + rk.PENALTY_CAP, "slowdown is capped", rk.rank_factor(30, 1))
check(rk.power_factor(14, 14, {6001}) < 1, "Bear Form makes fights faster", rk.power_factor(14, 14, {6001}))

m, town = rk.train_trip(("Darkshore", 37.0, 44.0), 12)
check(town == "Nighthaven" and m <= 0.5, "from 10, Teleport: Moonglade is the cheapest trainer trip", (m, town))

FAKE = {
    1: {"name": "A", "target_center": ("Darkshore", 40.0, 50.0)},
    2: {"name": "B", "target_center": ("Darkshore", 41.0, 51.0)},
    3: {"name": "C", "target_center": ("Darkshore", 70.0, 20.0)},
}
rk.quest = lambda q: FAKE.get(q)
groups = rk.clusters([1, 2, 3])
check(len(groups) == 2 and len(groups[0]["quests"]) == 2, "nearby objectives share one outing", groups)
corners = rk._simplify([(0.30, 0.86), (0.33, 0.86), (0.36, 0.86), (0.36, 0.83), (0.36, 0.80), (0.34, 0.80)], 0.012)
check(
    corners == [(0.30, 0.86), (0.36, 0.86), (0.36, 0.80), (0.34, 0.80)], "a walked path keeps only its corners", corners
)

sv = Path(tempfile.mkdtemp()) / "DruidKit.lua"
trail = ";".join(
    f"1432:{x:.3f},{y:.3f}"
    for x, y in [(0.30, 0.86), (0.33, 0.86), (0.36, 0.86), (0.36, 0.83), (0.36, 0.80), (0.34, 0.80)]
)
sv.write_text(f'DruidKitDB = {{ stepLog = {{ {{ i = 3, q = 86585, name = "Banner", trail = "{trail}" }} }} }}')
learned = rk.learned_paths(str(sv))
check(len(learned) == 1 and learned[0]["via"][0] == [1432, 36.0, 86.0], "a bent walk becomes via waypoints", learned)
# Hearthstone and flight paths in the simulator.
bad = rk.simulate(
    {
        "start": {"home": "Stormwind", "flights": ["Stormwind"], "at": "Menethil"},
        "events": [
            {"kind": "travel", "text": "Fly to Thelsamar"},
            {"kind": "hearth", "text": "Hearth to Thelsamar"},
        ],
    }
)["problems"]
check(any("flight to Thelsamar before" in p for p in bad), "flying to an unlearned flight path is a problem", bad)
check(any("hearthstone is set to Stormwind" in p for p in bad), "hearthing to the wrong town is a problem", bad)
check(any("Menethil (flight master) without learning" in p for p in bad), "passing a flight master without fp", bad)
good = rk.simulate(
    {
        "start": {"home": "Stormwind", "flights": ["Stormwind"], "at": "Menethil"},
        "events": [
            {"kind": "fp", "at": "Menethil"},
            {"kind": "travel", "text": "walk to Thelsamar"},
            {"kind": "fp", "at": "Thelsamar"},
            {"kind": "home", "at": "Thelsamar"},
            {"kind": "hearth", "text": "Hearth to Thelsamar"},
            {"kind": "travel", "text": "Fly to Menethil"},
        ],
    }
)
check(
    good["problems"] == [] and good["flight_paths_learned"] == ["Menethil", "Thelsamar"],
    "fp + home plan is clean",
    good,
)
cd = rk.simulate({"start": {"home": "Thelsamar"}, "events": [{"kind": "hearth"}, {"kind": "hearth"}]})["problems"]
check(any("cooldown" in p for p in cd), "two hearths inside the cooldown is a problem", cd)

# Route files: tools/route_check.py
sys.path.insert(0, str(ROOT / "tools"))
import route_check  # noqa: E402

ROUTE = {
    "sections": [
        {
            "title": "LM",
            "steps": [
                {"do": "turnin", "q": 1, "name": "x", "goto": ["Loch Modan", 34.0, 51.0]},
                {"do": "hearth", "to": "Thelsamar"},
                {"do": "fly", "to": "Ironforge", "where": "Thelsamar flight master"},
            ],
        }
    ]
}
err, warn = route_check.check(ROUTE, home="Stormwind", flights=["Stormwind, Elwynn"])
check(len(err) == 3, "hearth elsewhere + fly to and from unknown paths are errors", err)
check(any("never learns that flight path" in w for w in warn), "warns about the Thelsamar flight master", warn)
ROUTE["sections"][0]["steps"][1:1] = [{"do": "fp", "to": "Thelsamar"}, {"do": "home", "to": "Thelsamar"}]
err, warn = route_check.check(ROUTE, home="Stormwind", flights=["Stormwind, Elwynn", "Ironforge, Dun Morogh"])
check(err == [] and warn == [], "with fp and home steps the route is clean", (err, warn))
# Transport: Nighthaven only flies to Rut'theran; boats say where to board.
m, legs = rk.travel_route("Nighthaven", "Menethil")
check(
    [leg["how"] for leg in legs] == ["flight", "flight", "boat"] and legs[2].get("board"),
    "Nighthaven -> Menethil is two flights and a boat, with where to board",
    legs,
)
m2, legs2 = rk.travel_route("Nighthaven", "Auberdine", flights={"Nighthaven", "Rut'theran"})
check(legs2[-1]["how"] == "boat", "without the Auberdine flight path the second leg is the boat", legs2)
TR = {
    "sections": [
        {
            "title": "T",
            "steps": [
                {"do": "fly", "to": "Auberdine", "where": "Nighthaven flight master"},
                {"do": "goto", "text": "Boat to Menethil Harbor", "to": "Menethil Harbor"},
            ],
        }
    ]
}
err, warn = route_check.check(TR, home="Lakeshire", flights=["Nighthaven", "Rut'theran", "Auberdine"])
check(any("no direct flight Nighthaven -> Auberdine" in e for e in err), "two-hop flight in one step is an error", err)
check(any("transport step without how" in w for w in warn), "a boat step without directions is flagged", warn)
# Item plan: quest items for quests the route won't do soon -> bank (bank on the way) or drop (starter that drops).
saved_db = rk._DB
rk._DB = {
    "quests": {
        "161": {"name": "A Dark Threat Looms", "sourceItemId": 2563},
        "129": {"name": "A Free Lunch", "sourceItemId": 5534},
        "86613": {"name": "Excavation Tools"},
    },
    "items": {
        "2563": {"name": "Strange Smelling Powder"},
        "5534": {"name": "Parker's Lunch"},
        "278049": {"name": "Excavation Tools", "startQuest": 86613, "objectDrops": [665282]},
    },
    "objects": {"665282": {"name": "Excavation Tools pile"}},
    "npcs": {},
}
STATE = {
    "log": {"161": {}, "129": {}},
    "done": [],
    "inventory": {
        "Strange Smelling Powder": {"id": 2563},
        "Parker's Lunch": {"id": 5534},
        "Excavation Tools": {"id": 278049},
    },
}
ROUTE_IP = {
    "sections": [
        {
            "title": "T",
            "steps": [
                {"do": "note", "text": "Teleport"},
                {"do": "turnin", "q": 5061, "name": "Aquatic Form", "goto": ["Darnassus", 35.4, 8.4]},
                {"do": "turnin", "q": 129, "name": "A Free Lunch", "goto": ["Redridge Mountains", 10.2, 71.5]},
            ],
        }
    ]
}
plan = rk.item_plan(STATE, ROUTE_IP)
rk._DB = saved_db
check(
    plan.get("Strange Smelling Powder", {}).get("action") == "bank"
    and "Darnassus" in plan["Strange Smelling Powder"]["why"],
    "a quest item for a quest not in the route is banked at the next bank",
    plan,
)
check("Parker's Lunch" not in plan, "an item the route still needs stays in the bags", plan)
check(
    plan.get("Excavation Tools", {}).get("action") == "drop" and "drops again" in plan["Excavation Tools"]["why"],
    "a quest starter that drops again is dropped when the route doesn't do it",
    plan,
)

# RULES v13c: packed camps out, open beasts in
import importlib, sys as _s
_s.path.insert(0, str(HERE.parent / "planner")) if "HERE" in dir() else None
import rk as _rk
c20, c226 = _rk.crowd(20), _rk.crowd(226)
check(c20 and c20["packs"] >= 2.0 and c20["runners"], "Blackrock camp counts as packs of fleeing humanoids", c20)
check(c226 and c226["packs"] < 1.0 and not c226["runners"], "Duskwood wolves stand alone and don't flee", c226)
done("planner_test")
