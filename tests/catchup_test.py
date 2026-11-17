"""Reload or a new route id must not throw you back to step 1: the tracker catches up to the last quest you've
handed in. Abandon steps tick themselves, and steps with no map spot point the arrow at the next one that has."""

from lupa.lua51 import LuaRuntime

from expect import check, done
from wowenv import HERE, source

SRC = (HERE / "steps_test.py").read_text(encoding="utf-8")
OPEN = "L.execute(r" + '"' * 3
MOCKS = SRC.split(OPEN, 1)[1].split("DruidKitRoute = {")[0]

L = LuaRuntime(unpack_returned_tuples=True)
L.execute(MOCKS)
L.execute(r"""
function GetBindLocation() return "Lakeshire" end
ZONE = "Loch Modan"; SUB = "Stonewrought Dam"
LOG = { [1078] = { title = "Retrieval for Mauren" }, [436] = { title = "Ironband's Excavation", done = true } }
DONE = { [97926] = true, [353] = true, [199] = true }
DruidKitRoute = { id = "v4", sections = { { title = "S", steps = {
  { ["do"] = "abandon", qs = { 1078, 176 }, text = "Retrieval for Mauren and Hogger" },          -- 1
  { ["do"] = "turnin", q = 97926, name = "Making Do", at = { "Darkshore", 37.4, 40.1 } },        -- 2
  { ["do"] = "goto", text = "Boat to Menethil Harbor", to = "Menethil Harbor" },                  -- 3
  { ["do"] = "turnin", q = 353, name = "Stormpike's Delivery", at = { "Loch Modan", 24.8, 18.4 } }, -- 4
  { ["do"] = "fp", to = "Thelsamar", at = { "Loch Modan", 33.9, 51.0 } },                         -- 5
  { ["do"] = "accept", q = 255, name = "Mercenaries", at = { "Loch Modan", 34.6, 44.5 } },        -- 6
  { ["do"] = "turnin", q = 199, name = "A Dark Threat Looms", at = { "Loch Modan", 46.1, 13.6 } }, -- 7
  { ["do"] = "accept", q = 161, name = "A Dark Threat Looms", at = { "Loch Modan", 46.1, 13.6 } }, -- 8
  { ["do"] = "complete", q = 255, name = "Mercenaries", at = { "Loch Modan", 70.8, 22.8 } },      -- 9
  { ["do"] = "goto", text = "Walk on", to = "Somewhere" },                                         -- 10
  { ["do"] = "turnin", q = 436, name = "Ironband's Excavation", at = { "Loch Modan", 64.9, 66.7 } }, -- 11
} } } }
DruidKitDB = { routeId = "v3", routeStep = 9 }
""")
L.execute(source("DruidKit/DruidKit_Steps.lua"))
L.execute(r"""
ev = nil
for _, f in ipairs(frames) do if f.events and f.events.QUEST_DETAIL then ev = f end end
function fire(e, a) ev.on_OnEvent(ev, e, a) end
R = {}
fire("PLAYER_LOGIN")
R[#R+1] = DruidKitDB.routeStep               -- new route id: catch-up to after the 199 hand-in (step 8)
R[#R+1] = DruidKitDB.passedQ[255] == true    -- Mercenaries was passed (not in the log)
R[#R+1] = DruidKitDB.manual[1] == true or false   -- abandon step not ticked by hand...
LOG[1078] = nil; DruidKit_StepsEvaluate()
R[#R+1] = DruidKitDB.routeStep               -- still 8 (abandon was behind, passed)
DONE[161] = true; LOG[161] = nil
LOG[161] = { title = "A Dark Threat Looms" }; DruidKit_StepsEvaluate()
R[#R+1] = DruidKitDB.routeStep               -- 161 accepted -> Mercenaries complete is skipped (passed) -> step 10
R[#R+1] = GOTO[#GOTO]                         -- step 10 has no spot: arrow points at step 11
-- a reload keeps the place
fire("PLAYER_LOGIN")
R[#R+1] = DruidKitDB.routeStep
""")
r = list(L.globals().R.values())
print(r)
check(r[0] == 8, "a new route id catches up to just after the last handed-in quest", r[0])
check(r[1] is True, "quests passed on the way are remembered as behind you", r[1])
check(r[3] == 8, "catch-up holds after re-evaluation", r[3])
check(r[4] == 10, "a passed quest's later steps don't block the route", r[4])
check(r[5] == "Loch Modan 64.9,66.7", "a step with no spot points the arrow at the next spot", r[5])
check(r[6] == 10, "a reload keeps your place", r[6])

# Abandon step ticks itself once the quests are gone from the log.
A = LuaRuntime(unpack_returned_tuples=True)
A.execute(MOCKS)
A.execute(r"""
LOG = { [1078] = { title = "Retrieval for Mauren" } }
DruidKitRoute = { id = "a", sections = { { title = "S", steps = {
  { ["do"] = "abandon", qs = { 1078, 176 }, text = "Retrieval for Mauren and Hogger" },
  { ["do"] = "note", text = "next" },
} } } }
""")
A.execute(source("DruidKit/DruidKit_Steps.lua"))
A.execute(r"""
for _, f in ipairs(frames) do if f.events and f.events.QUEST_DETAIL then ev = f end end
ev.on_OnEvent(ev, "PLAYER_LOGIN")
R = { DruidKitDB.routeStep, DruidKitSteps.main.text }
LOG[1078] = nil; DruidKit_StepsEvaluate()
R[3] = DruidKitDB.routeStep
""")
a = list(A.globals().R.values())
check(a[0] == 1 and "Abandon" in str(a[1]), "abandon step waits while the quest is in the log", a[:2])
check(a[2] == 2, "abandon step ticks itself when the quest is gone", a[2])
done("catchup_test")
