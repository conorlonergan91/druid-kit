"""Steps: known flight paths use ClaudeProgress's character key (cached realm when GetRealmName reads "" at login);
goto/fly/hearth tick on the destination town exactly, or on the zone only when the destination is the zone."""

from lupa.lua51 import LuaRuntime

from expect import check, done
from wowenv import HERE, source

SRC = (HERE / "steps_test.py").read_text(encoding="utf-8")
OPEN = "L.execute(r" + '"' * 3
MOCKS = SRC.split(OPEN, 1)[1].split("DruidKitRoute = {")[0]


def run(setup, then):
    L = LuaRuntime(unpack_returned_tuples=True)
    L.execute(MOCKS)
    L.execute(setup)
    L.execute(source("DruidKit/DruidKit_Steps.lua"))
    L.execute(
        r"""
for _, f in ipairs(frames) do if f.events and f.events.QUEST_DETAIL then ev = f end end
ev.on_OnEvent(ev, "PLAYER_LOGIN")
R = {}
"""
        + then
    )
    return L.globals().R


R = run(
    r"""
function UnitName() return "Cu" end
function GetRealmName() return "" end
GetNormalizedRealmName = nil
ClaudeProgressDB = { _realm = "R5", flights = { ["Cu-R5"] = { ["Thelsamar, Loch Modan"] = true } } }
DruidKitRoute = { id = "rk", sections = { { title = "S", steps = {
  { ["do"] = "fp", to = "Thelsamar" },
  { ["do"] = "note", text = "Kill things" },
} } } }
""",
    "DruidKit_StepsEvaluate(); R[1] = DruidKitDB.routeStep",
)
check(R[1] == 2, "empty realm at login: the cached realm finds the known flight path", R[1])

STEPS = r"""
DruidKitRoute = { id = "pl", sections = { { title = "S", steps = {
  { ["do"] = "goto", text = "Walk to Goldshire", to = "Goldshire, Elwynn Forest" },
  { ["do"] = "note", text = "Stop 1" },
  { ["do"] = "goto", text = "Into Elwynn", to = "Elwynn Forest" },
  { ["do"] = "note", text = "Stop 2" },
  { ["do"] = "hearth", to = "Stormwind" },
  { ["do"] = "note", text = "Stop 3" },
} } } }
"""
R = run(
    STEPS,
    r"""
ZONE = "Elwynn Forest"; SUB = "Northshire Valley"; DruidKit_StepsEvaluate(); R[1] = DruidKitDB.routeStep
ZONE = "Elwynn Forest"; SUB = "Goldshire Lake"; DruidKit_StepsEvaluate(); R[2] = DruidKitDB.routeStep
SUB = "goldshire"; DruidKit_StepsEvaluate(); R[3] = DruidKitDB.routeStep
DruidKit_StepDone(); SUB = "Northshire Valley"; DruidKit_StepsEvaluate(); R[4] = DruidKitDB.routeStep
DruidKit_StepDone(); ZONE = "Stormwind City"; SUB = "Trade District"; DruidKit_StepsEvaluate(); R[5] = DruidKitDB.routeStep
""",
)
check(R[1] == 1, "elsewhere in Elwynn Forest doesn't tick a Goldshire step", R[1])
check(R[2] == 1, "a subzone that only contains the town's name doesn't tick it", R[2])
check(R[3] == 2, "the Goldshire subzone ticks it (any case)", R[3])
check(R[4] == 4, "a step whose destination is the zone ticks anywhere in it", R[4])
check(R[5] == 6, "a Stormwind hearth step ticks in Stormwind City", R[5])
done("r2_steps_place_test")
