"""Update tidy-up: read the SavedVariables without lupa, and drop done steps from the route."""

import json
import sys
import tempfile
from pathlib import Path

from expect import check, done
from wowenv import ROOT

sys.path.insert(0, str(ROOT / "tools"))
import prune_route  # noqa: E402
import save_state  # noqa: E402

CP = r"""
ClaudeProgressDB = {
["Cu-R5"] = {
["savedAt"] = "2026-11-18 01:17",
["basics"] = { ["level"] = 20, ["zone"] = "Loch Modan", ["xp"] = 6875, },
["bags"] = { ["total"] = 56, ["free"] = 11, },
["quests"] = {
{ ["title"] = "Mercenaries", ["id"] = 255, ["objectives"] = { { ["done"] = false, ["text"] = "0/4" }, }, }, -- [1]
{ ["title"] = "A \"Dark\" Threat", ["id"] = 161, ["complete"] = true, }, -- [2]
},
["completed"] = { ["count"] = 2, ["quests"] = { [86758] = "Twisting the Knife", [258] = true, }, },
["travel"] = { ["home"] = "Lakeshire", ["flights"] = { "Thelsamar, Loch Modan", }, ["hearthCooldown"] = 0, },
},
}
"""
DK = 'DruidKitDB = { ["routeId"] = "r1", ["routeStep"] = 3, ["manual"] = { [1] = true, }, ["skipQ"] = { [86613] = {} }, }'
tmp = Path(tempfile.mkdtemp())
(tmp / "cp.lua").write_text(CP, encoding="utf-8")
(tmp / "dk.lua").write_text(DK, encoding="utf-8")
s = save_state.state(str(tmp / "cp.lua"), str(tmp / "dk.lua"))
check(s["level"] == 20 and s["bags_free"] == 11, "basics and bags read", s)
check(
    set(s["log"]) == {255, 161} and s["log"][161]["complete"] and not s["log"][255]["complete"], "quest log", s["log"]
)
check(s["log"][161]["title"] == 'A "Dark" Threat', "escaped quotes in titles", s["log"][161])
check(s["done"] == [258, 86758] and s["travel"]["home"] == "Lakeshire", "completed quests and travel", s)
check(
    s["route"] == {"id": "r1", "step": 3, "manual": [1], "skipped": ["86613"], "passed": []}, "route state", s["route"]
)

s = json.loads(json.dumps(s))  # as the update stores it
ROUTE = {
    "id": "r1",
    "sections": [
        {
            "title": "Old",
            "steps": [
                {"do": "complete", "q": 86758, "name": "Knife"},  # before the saved step
                {"do": "turnin", "q": 86613, "name": "Tools"},  # before the saved step (skipped)
                {"do": "complete", "q": 255, "name": "Mercenaries"},  # current: keep
                {"do": "turnin", "q": 255, "name": "Mercenaries"},  # keep
            ],
        },
        {
            "title": "Next",
            "steps": [
                {"do": "fp", "to": "Thelsamar"},  # known: drop
                {"do": "home", "to": "Lakeshire"},  # set: drop
                {"do": "level", "level": 20},  # reached: drop
                {"do": "turnin", "q": 161, "name": "Dark Threat"},  # keep (in log, not handed in)
                {"do": "level", "level": 21},  # keep
            ],
        },
    ],
}
out, n = prune_route.prune(ROUTE, s)
names = [(st["do"], st.get("q") or st.get("level") or st.get("to")) for sec in out["sections"] for st in sec["steps"]]
check(n == 5, "five done steps removed", n)
check(names == [("complete", 255), ("turnin", 255), ("turnin", 161), ("level", 21)], "the right steps stay", names)
s["route"]["id"] = "other"
out, n = prune_route.prune(ROUTE, s)
check(n == 5 and out["sections"][0]["steps"][0]["q"] == 255, "a different route id prunes by state alone", n)
done("prune_test")
