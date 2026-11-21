"""planner/rk.py simulator and item plan on fake data (no db.json): last-event level, unknown quests, training
with no start spot, flight paths, item grouping, objective counts, SavedVariables read without Lua."""

import sys
import tempfile
from pathlib import Path

from expect import check, done
from wowenv import ROOT

sys.path.insert(0, str(ROOT / "planner"))
import rk  # noqa: E402


def fake_db(quests=None, items=None, npcs=None):
    rk._DB = {"quests": quests or {}, "items": items or {}, "npcs": npcs or {}, "objects": {}}
    rk.quest.cache_clear()
    rk._CROWD.clear()
    rk._ZIDX.clear()


fake_db()
sim = rk.simulate({"start": {"level": 19}, "events": [{"kind": "grind", "to": 20}]})
check(sim["hours_to_20"] is not None and sim["hours_to_20"] == sim["hours"], "level 20 on the last event counts", sim)

bad = rk.simulate({"start": {"level": 5}, "events": [{"kind": "accept", "q": 999}, {"kind": "turnin", "q": 999}]})
check(sum("999: no such quest" in p for p in bad["problems"]) == 2, "unknown quest ids are problems", bad["problems"])

check(
    rk.train_trip(None, 12) == (rk.UNKNOWN_TRIP_MIN, None),
    "no start spot: a fixed trainer trip",
    rk.train_trip(None, 12),
)
sim = rk.simulate({"start": {"level": 12}, "events": [{"kind": "train"}]})
check(sim["hours"] > 0, "training from an unknown spot costs time", sim)

lakeshire, ironforge, stormwind = (rk.towns()[t] for t in ("Lakeshire", "Ironforge", "Stormwind"))
a = (lakeshire["zone"], lakeshire["x"], lakeshire["y"])
b = (ironforge["zone"], ironforge["x"], ironforge["y"])
check(rk.move_min(a, b, flights=set()) > rk.move_min(a, b), "no known flights: the trip is longer", "")
c = (stormwind["zone"], stormwind["x"], stormwind["y"])
far = rk.move_min(c, (rk.towns()["Menethil"]["zone"], 10.0, 60.0), flights=set())
check(far < float("inf"), "a trip travel.json can't route without flights still has a cost", far)
fly = {"kind": "travel", "text": "Fly to Ironforge"}
known = rk.simulate({"start": {"at": "Lakeshire", "flights": ["Lakeshire", "Stormwind", "Ironforge"]}, "events": [fly]})
unknown = rk.simulate({"start": {"at": "Lakeshire", "flights": []}, "events": [fly]})
check(known["hours"] > 0, "travel events cost time", known)
check(unknown["hours"] > known["hours"], "the simulator only flies the flight paths it knows", (known, unknown))

fake_db(
    quests={
        "1": {"name": "Kill", "objectives": {"1": [[5534, "Wolves"]]}},
        "2": {"name": "Collect", "objectives": [None, None, [[2563, "Powder"]]]},
    },
    items={"5534": {"name": "Not an objective"}, "2563": {"name": "Powder"}},
)
state = {"log": {"1": {}, "2": {}}, "done": [], "inventory": {"Lunch": {"id": 5534}, "Powder": {"id": 2563}}}
route = {"sections": [{"title": "T", "steps": [{"do": "goto", "goto": ["Darnassus", 35.0, 8.0]}]}]}
plan = rk.item_plan(state, route)
check("Lunch" not in plan, "a creature id that matches an item id is not a quest item", plan)
check(plan.get("Powder", {}).get("action") == "bank", "list-shaped item objectives are quest items", plan)

check(rk._count_from_text({"objectivesText": ["Kill 10 Wolves and 8 Bears."]}, 2) == 18, "counts add per objective", "")
check(rk._count_from_text({"objectivesText": ["Bring 8 Meat to Bob in 5 minutes."]}, 1) == 8, "one objective: max", "")
fake_db(
    quests={"3": {"name": "Two", "objectives": {"1": [[30], [31]]}, "objectivesText": ["Kill 10 A and 8 B."]}},
    npcs={"30": {"name": "A"}, "31": {"name": "B"}},
)
check(rk.quest(3)["kills"] == 18, "a two-mob quest needs both counts", rk.quest(3)["kills"])

sv = Path(tempfile.mkdtemp()) / "DruidKit.lua"
sv.write_text(
    'DruidKitDB = { stepLog = { { ["do"] = "complete", secs = 120, xp = 300, est = 1 }, '
    '{ ["do"] = "goto", secs = 60, xp = 0 } } }\nos.execute("touch /tmp/nope")\n',
    encoding="utf-8",
)
try:
    cal = rk.calibrate(str(sv))
except ValueError as e:
    cal = e
check(isinstance(cal, ValueError), "SavedVariables are parsed as data, never run", cal)
sv.write_text('DruidKitDB = { stepLog = { { ["do"] = "complete", secs = 120, xp = 300, est = 1 } } }', encoding="utf-8")
cal = rk.calibrate(str(sv))
check(cal["actual_over_est"] == 2.0 and cal["steps"] == 1, "calibrate reads the step log", cal)
done("py_rk_test")
