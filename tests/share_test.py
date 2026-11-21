"""Quests a friend shares: their accept steps are done at once (the quest is in your log), the shared quest is
auto-accepted when it's in the route, and a trip that only served those quests (onlyFor) is skipped."""

from lupa.lua51 import LuaRuntime

from expect import check, done
from wowenv import HERE, source

SRC = (HERE / "steps_test.py").read_text(encoding="utf-8")
OPEN = "L.execute(r" + '"' * 3
MOCKS = SRC.split(OPEN, 1)[1].split("DruidKitRoute = {")[0]
L = LuaRuntime(unpack_returned_tuples=True)
L.execute(MOCKS)
L.execute(r"""
DruidKitRoute = { id = "sh", sections = { { title = "Dungeon prep", steps = {
  { ["do"] = "fly", to = "Lakeshire", onlyFor = { 132 }, at = { "Stormwind City", 71.0, 72.5 } },
  { ["do"] = "accept", q = 132, name = "The Defias Brotherhood", at = { "Redridge Mountains", 21.4, 45.4 } },
  { ["do"] = "accept", q = 214, name = "Red Silk Bandanas", at = { "Westfall", 56.7, 47.4 } },
  { ["do"] = "note", text = "Pack for the dungeon" },
} } } }
DruidKitDB = {}
ZONE = "Stormwind City"; SUB = "Trade District"
""")
L.execute(source("DruidKit/DruidKit_Steps.lua"))
L.execute(r"""
for _, f in ipairs(frames) do if f.events and f.events.QUEST_DETAIL then ev = f end end
function fire(e, a) ev.on_OnEvent(ev, e, a) end
fire("PLAYER_LOGIN")
R = { DruidKitDB.routeStep }
-- a friend shares The Defias Brotherhood: the game shows the quest window
CURQ = 132; CURTITLE = "The Defias Brotherhood"; fire("QUEST_DETAIL")
R[2] = ACCEPTED
DruidKit_StepsEvaluate()
R[3] = DruidKitDB.routeStep
-- and Red Silk Bandanas
CURQ = 214; CURTITLE = "Red Silk Bandanas"; fire("QUEST_DETAIL"); DruidKit_StepsEvaluate()
R[4] = DruidKitDB.routeStep
""")
r = list(L.globals().R.values())
print(r)
check(r[0] == 1, "starts on the flight to the quest giver", r[0])
check(r[1] == 132, "a shared route quest is accepted for you", r[1])
check(r[2] == 3, "the flight and accept for a shared quest are skipped", r[2])
check(r[3] == 4, "each shared quest ticks its accept step", r[3])
done("share_test")
