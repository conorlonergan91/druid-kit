"""Dungeon steps marked `inside` show no arrow (the game gives no position there): not their own spot, not the next
step's outside, and a route arrow left from before is cleared (one the player set stays)."""

from lupa.lua51 import LuaRuntime

from expect import check, done
from wowenv import HERE, source

SRC = (HERE / "steps_test.py").read_text(encoding="utf-8")
OPEN = "L.execute(r" + '"' * 3
MOCKS = SRC.split(OPEN, 1)[1].split("DruidKitRoute = {")[0]
L = LuaRuntime(unpack_returned_tuples=True)
L.execute(MOCKS)
L.execute(r"""
NAV = "route"; CLEARED = 0
function DruidKit_NavTarget() return NAV and { owner = NAV } end
function DruidKit_NavClear() NAV = nil; CLEARED = CLEARED + 1 end
DruidKitRoute = { id = "in", sections = { { title = "Deadmines", steps = {
  { ["do"] = "goto", text = "Walk to the mine", to = "Moonbrook", at = { "Westfall", 42.6, 71.8 } },
  { ["do"] = "note", text = "Kill Rhahk'Zor", inside = true },
  { ["do"] = "complete", q = 7, name = "Oh Brother", inside = true, at = { "The Deadmines", 50, 50 } },
  { ["do"] = "turnin", q = 7, name = "Oh Brother", npc = "Wilder", at = { "Stormwind City", 65, 21 } },
} } } }
DruidKitDB = {}
""")
L.execute(source("DruidKit/DruidKit_Steps.lua"))
L.execute(r"""
for _, f in ipairs(frames) do if f.events and f.events.QUEST_DETAIL then ev = f end end
ev.on_OnEvent(ev, "PLAYER_LOGIN")
LOG[7] = { title = "Oh Brother" }
DruidKit_ToggleSteps(true)
R = { GOTO[#GOTO] }
GOTO = {}
DruidKitDB.manual[1] = true; DruidKit_StepsEvaluate()
R[2] = DruidKitDB.routeStep; R[3] = #GOTO; R[4] = CLEARED
DruidKitDB.manual[2] = true; DruidKit_StepsEvaluate()
R[5] = DruidKitDB.routeStep; R[6] = #GOTO
""")
r = list(L.globals().R.values())
print(r, list(L.globals().GOTO.values()))
check(r[0] == "Westfall 42.6,71.8", "outside, the step's own spot gets the arrow", r[0])
check(r[1] == 2 and r[2] == 0, "an inside step points nowhere, not even at the hand-in outside", r[2])
check(r[3] >= 1, "the arrow left from the walk there is cleared", r[3])
check(r[4] == 3 and r[5] == 0, "an inside step with a spot still gets no arrow", r[5])

L.execute(r"""
NAV = "way"; CLEARED = 0; DruidKit_StepsCommand("reset")
DruidKitDB.manual[1] = true; DruidKit_StepsEvaluate()
R = { DruidKitDB.routeStep, CLEARED, NAV }
""")
r = list(L.globals().R.values())
check(r[0] == 2 and r[1] == 0 and r[2] == "way", "a /way arrow survives moving to an inside step", r)
done("r5_steps_inside_test")
