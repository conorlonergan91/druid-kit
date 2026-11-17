"""Navigation: waypoints on the way (via), breadcrumb trail in the step log, and the stuck warning."""

from lupa.lua51 import LuaRuntime

from expect import check, done
from wowenv import HERE, source

SRC = (HERE / "steps_test.py").read_text(encoding="utf-8")
OPEN = "L.execute(r" + '"' * 3
MOCKS = SRC.split(OPEN, 1)[1].split("DruidKitRoute = {")[0]

L = LuaRuntime(unpack_returned_tuples=True)
L.execute(MOCKS)
L.execute(r"""
POS = { 0.30, 0.86 }
C_Map = C_Map or {}
C_Map.GetBestMapForUnit = function() return 1432 end
C_Map.GetPlayerMapPosition = function() return { GetXY = function() return POS[1], POS[2] end } end
DruidKitRoute = { id = "t3", sections = { { title = "Loch Modan", steps = {
  { ["do"] = "complete", q = 86585, name = "Banner of the Fallen", text = "Raise the banner",
    via = { { "Loch Modan", 36.0, 80.0, "east side path" }, { "Loch Modan", 33.0, 84.0, "cave entrance" } },
    at = { "Loch Modan", 31.4, 85.0 } },
  { ["do"] = "accept", q = 92, name = "Goulash", npc = "Breanna" },
} } } }
""")
L.execute(source("DruidKit/DruidKit_Steps.lua"))
L.execute(r"""
ev = nil
for _, f in ipairs(frames) do if f.events and f.events.QUEST_DETAIL then ev = f end end
function fire(e, a) ev.on_OnEvent(ev, e, a) end
function cur() return DruidKitDB.routeStep end
LOG[86585] = { title = "Banner of the Fallen", done = false }
fire("PLAYER_LOGIN")
R = {}
R[#R+1] = GOTO[#GOTO]                  -- first waypoint
DruidKit_OnArrive("x")
R[#R+1] = GOTO[#GOTO]                  -- second waypoint
DruidKit_OnArrive("x")
R[#R+1] = GOTO[#GOTO]                  -- the step's own spot
R[#R+1] = cur()                        -- still on the step (a kill step isn't done by arriving)
for i = 1, 5 do POS[1] = POS[1] + 0.01; ev.on_OnUpdate(ev, 2.1) end
LOG[86585].done = true; fire("QUEST_LOG_UPDATE")
R[#R+1] = cur()
R[#R+1] = DruidKitDB.stepLog[#DruidKitDB.stepLog].trail or ""
R[#R+1] = DruidKitDB.stepLog[#DruidKitDB.stepLog].target or ""
DruidKit_OnNavStuck("the cave")
R[#R+1] = printed[#printed]
""")
r = list(L.globals().R.values())
print(r)
check("36.0,80.0" in str(r[0]) or "36,80" in str(r[0]), "arrow starts at the first waypoint", r[0])
check("33" in str(r[1]) and "84" in str(r[1]), "then the second waypoint", r[1])
check("31.4" in str(r[2]), "then the step's own spot", r[2])
check(r[3] == 1 and r[4] == 2, "arriving doesn't finish a kill step; objectives do", r[3:5])
check(str(r[5]).count(";") >= 3 and "1432:" in str(r[5]), "the walked path is saved with the step", r[5])
check("Loch Modan:31.4,85" in str(r[6]), "the step's target is saved for the planner", r[6])
check("not getting closer" in str(r[7]), "stuck warning in words", r[7])
done("via_test")
