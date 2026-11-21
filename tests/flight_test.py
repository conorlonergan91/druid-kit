"""Fly steps tick when you take a flight to their town, not when you reach the flight master; a wrong town says so."""

from lupa.lua51 import LuaRuntime

from expect import check, done
from wowenv import HERE, source

SRC = (HERE / "steps_test.py").read_text(encoding="utf-8")
OPEN = "L.execute(r" + '"' * 3
MOCKS = SRC.split(OPEN, 1)[1].split("DruidKitRoute = {")[0]
L = LuaRuntime(unpack_returned_tuples=True)
L.execute(MOCKS)
L.execute(r"""
HOOKS = {}
function hooksecurefunc(name, f) HOOKS[name] = f end
function TakeTaxiNode(i) if HOOKS.TakeTaxiNode then HOOKS.TakeTaxiNode(i) end end
NODES = { "Ironforge, Dun Morogh", "Menethil Harbor, Wetlands" }
function TaxiNodeName(i) return NODES[i] end
ZONE = "Stormwind City"; SUB = "Trade District"
DruidKitRoute = { id = "fl", sections = { { title = "S", steps = {
  { ["do"] = "fly", to = "Menethil Harbor", npc = "Dungar Longdrink", at = { "Stormwind City", 71.0, 72.5 } },
  { ["do"] = "note", text = "Food and drink for the run" },
} } } }
DruidKitDB = {}
""")
L.execute(source("DruidKit/DruidKit_Steps.lua"))
L.execute(r"""
for _, f in ipairs(frames) do if f.events and f.events.QUEST_DETAIL then ev = f end end
ev.on_OnEvent(ev, "PLAYER_LOGIN")
DruidKit_ToggleSteps(true)
DruidKit_OnArrive("x", "route"); DruidKit_StepsEvaluate()
R = { DruidKitDB.routeStep }
TakeTaxiNode(1); DruidKit_StepsEvaluate()
R[2] = DruidKitDB.routeStep; R[3] = printed[#printed] or ""
TakeTaxiNode(2); DruidKit_StepsEvaluate()
R[4] = DruidKitDB.routeStep
""")
r = list(L.globals().R.values())
print(r)
check(r[0] == 1, "reaching the flight master does not tick the fly step", r[0])
check(r[1] == 1 and "goes to Ironforge" in r[2], "a flight to another town does not tick it, and says so", r[2])
check(r[3] == 2, "taking the flight to Menethil ticks it", r[3])
done("flight_test")
