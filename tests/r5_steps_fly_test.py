"""Fly steps tick only on a flight to the step's town (TakeTaxiNode to it) or on arriving in that town: never at the
flight master, on opening the flight map there, or on reaching the arrow's spot (the flight master)."""

from lupa.lua51 import LuaRuntime

from expect import check, done
from wowenv import HERE, source

SRC = (HERE / "steps_test.py").read_text(encoding="utf-8")
OPEN = "L.execute(r" + '"' * 3
MOCKS = SRC.split(OPEN, 1)[1].split("DruidKitRoute = {")[0]


def run(then):
    L = LuaRuntime(unpack_returned_tuples=True)
    L.execute(MOCKS)
    L.execute(r"""
HOOKS = {}
function hooksecurefunc(name, f) HOOKS[name] = f end
function TakeTaxiNode(i) if HOOKS.TakeTaxiNode then HOOKS.TakeTaxiNode(i) end end
NODES = { "Stormwind, Elwynn", "Menethil Harbor, Wetlands" }
function NumTaxiNodes() return #NODES end
function TaxiNodeName(i) return NODES[i] end
function TaxiNodeGetType(i) return i == 1 and "CURRENT" or "REACHABLE" end
function UnitName() return "Me" end
function GetRealmName() return "R" end
ClaudeProgressDB = { flights = { ["Me-R"] = { ["Menethil Harbor, Wetlands"] = true, ["Stormwind, Elwynn"] = true } } }
ZONE = "Stormwind City"; SUB = "Trade District"
DruidKitRoute = { id = "fl2", sections = { { title = "S", steps = {
  { ["do"] = "fly", to = "Menethil Harbor", npc = "Dungar Longdrink", at = { "Stormwind City", 71.0, 72.5 } },
  { ["do"] = "note", text = "Food and drink" },
} } } }
DruidKitDB = {}
""")
    L.execute(source("DruidKit/DruidKit_Steps.lua"))
    L.execute(
        r"""
for _, f in ipairs(frames) do if f.events and f.events.QUEST_DETAIL then ev = f end end
ev.on_OnEvent(ev, "PLAYER_LOGIN")
DruidKit_ToggleSteps(true)
R = {}
"""
        + then
    )
    return list(L.globals().R.values())


r = run(r"""
DruidKit_OnArrive("x", "route"); DruidKit_StepsEvaluate(); R[1] = DruidKitDB.routeStep
ev.on_OnEvent(ev, "TAXIMAP_OPENED"); DruidKit_StepsEvaluate(); R[2] = DruidKitDB.routeStep
ev.on_OnEvent(ev, "TAXIMAP_CLOSED"); ev.on_OnEvent(ev, "ZONE_CHANGED"); DruidKit_StepsEvaluate(); R[3] = DruidKitDB.routeStep
SUB = "Dun Modr"; ZONE = "Wetlands"; DruidKit_StepsEvaluate(); R[4] = DruidKitDB.routeStep
SUB = "Menethil Harbor"; DruidKit_StepsEvaluate(); R[5] = DruidKitDB.routeStep
""")
print(r)
check(r[0] == 1, "reaching the flight master (the arrow's spot) does not tick it", r[0])
check(r[1] == 1, "opening the flight map at the flight master does not tick it", r[1])
check(r[2] == 1, "closing the map without flying does not tick it", r[2])
check(r[3] == 1, "landing in the zone but not the town does not tick it", r[3])
check(r[4] == 2, "arriving in the town ticks it", r[4])

r = run(r"""
TakeTaxiNode(1); DruidKit_StepsEvaluate(); R[1] = DruidKitDB.routeStep
TakeTaxiNode(2); DruidKit_StepsEvaluate(); R[2] = DruidKitDB.routeStep
""")
check(r[0] == 1, "a flight to another town does not tick it", r[0])
check(r[1] == 2, "taking the flight to the step's town ticks it", r[1])
done("r5_steps_fly_test")
