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
done("planner_test")
