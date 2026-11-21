"""Two quests with the same title (Forever: Explosive Consultation x2): each name-only step counts its own hand-in."""

from lupa.lua51 import LuaRuntime

from expect import check, done
from wowenv import HERE, source

SRC = (HERE / "steps_test.py").read_text(encoding="utf-8")
OPEN = "L.execute(r" + '"' * 3
MOCKS = SRC.split(OPEN, 1)[1].split("DruidKitRoute = {")[0]
L = LuaRuntime(unpack_returned_tuples=True)
L.execute(MOCKS)
L.execute(r"""
DruidKitRoute = { id = "t2", sections = { { title = "S", steps = {
  { ["do"] = "accept", name = "Explosive Consultation", at = { "Westfall", 52.5, 53.0 } },
  { ["do"] = "turnin", name = "Explosive Consultation", at = { "Stormwind City", 63, 37 } },
  { ["do"] = "accept", name = "Explosive Consultation", at = { "Stormwind City", 63, 37 } },
  { ["do"] = "turnin", name = "Explosive Consultation", at = { "Westfall", 52.5, 53.0 } },
  { ["do"] = "note", text = "end" },
} } } }
DruidKitDB = {}
TITLES[90001] = "Explosive Consultation"; TITLES[90002] = "Explosive Consultation"
""")
L.execute(source("DruidKit/DruidKit_Steps.lua"))
L.execute(r"""
for _, f in ipairs(frames) do if f.events and f.events.QUEST_DETAIL then ev = f end end
function fire(e, a) ev.on_OnEvent(ev, e, a) end
fire("PLAYER_LOGIN")
R = {}
LOG[90001] = { title = "Explosive Consultation" }; DruidKit_StepsEvaluate()
R[1] = DruidKitDB.routeStep                -- 2: hand in the first
LOG[90001] = nil; DONE[90001] = true; fire("QUEST_TURNED_IN", 90001); DruidKit_StepsEvaluate()
R[2] = DruidKitDB.routeStep                -- 3: accept the second (not auto-done)
LOG[90002] = { title = "Explosive Consultation" }; DruidKit_StepsEvaluate()
R[3] = DruidKitDB.routeStep                -- 4: hand in the second (not auto-done)
LOG[90002] = nil; DONE[90002] = true; fire("QUEST_TURNED_IN", 90002); DruidKit_StepsEvaluate()
R[4] = DruidKitDB.routeStep                -- 5
""")
r = list(L.globals().R.values())
print(r)
check(r == [2, 3, 4, 5], "each step of a repeated title waits for its own quest", r)
done("sametitle_test")
