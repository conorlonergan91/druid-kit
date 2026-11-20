"""A pre-dungeon step can require free bag spaces: it shows the count and ticks itself at the target."""
from lupa.lua51 import LuaRuntime
from expect import check, done
from wowenv import HERE, source

SRC = (HERE / "steps_test.py").read_text(encoding="utf-8")
OPEN = "L.execute(r" + '"' * 3
MOCKS = SRC.split(OPEN, 1)[1].split("DruidKitRoute = {")[0]
L = LuaRuntime(unpack_returned_tuples=True)
L.execute(MOCKS)
L.execute(r"""
FREE = 12
C_Container = { GetContainerNumFreeSlots = function(b) return b == 0 and FREE or 0 end }
DruidKitRoute = { id = "fb", sections = { { title = "S", steps = {
  { ["do"] = "note", text = "Before the dungeon: sell, repair and bank", freeBags = 20 },
  { ["do"] = "note", text = "Find a group" },
} } } }
DruidKitDB = {}
""")
L.execute(source("DruidKit/DruidKit_Steps.lua"))
L.execute(r"""
for _, f in ipairs(frames) do if f.events and f.events.QUEST_DETAIL then ev = f end end
ev.on_OnEvent(ev, "PLAYER_LOGIN")
DruidKit_ToggleSteps(true)
R = { DruidKitDB.routeStep, DruidKitSteps.detail.text }
FREE = 21; DruidKit_StepsEvaluate()
R[3] = DruidKitDB.routeStep
""")
r = list(L.globals().R.values())
print(r)
check(r[0] == 1 and "12 of 20" in r[1], "shows free bag spaces against the 20 needed", r[1])
check(r[2] == 2, "ticks itself at 20+ free spaces", r[2])
done("freebags_test")
