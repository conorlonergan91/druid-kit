"""A rebuilt route (new id) keeps the steps you ticked by hand (notes, training, travel), matched by kind + text."""

from lupa.lua51 import LuaRuntime

from expect import check, done
from wowenv import HERE, source

SRC = (HERE / "steps_test.py").read_text(encoding="utf-8")
OPEN = "L.execute(r" + '"' * 3
MOCKS = SRC.split(OPEN, 1)[1].split("DruidKitRoute = {")[0]


def login(route_lua, db_lua):
    L = LuaRuntime(unpack_returned_tuples=True)
    L.execute(MOCKS)
    L.execute(route_lua + "\n" + db_lua)
    L.execute(source("DruidKit/DruidKit_Steps.lua"))
    L.execute(r"""
for _, f in ipairs(frames) do if f.events and f.events.QUEST_DETAIL then ev = f end end
ev.on_OnEvent(ev, "PLAYER_LOGIN")
DruidKit_ToggleSteps(true)
""")
    return L


A = """DruidKitRoute = { id = "a", sections = { { title = "S", steps = {
  { ["do"] = "note", text = "Sell before the trip" },
  { ["do"] = "note", text = "Bank: make room" },
} } } }"""
B = A.replace('id = "a"', 'id = "b"').replace(
    '{ ["do"] = "note", text = "Sell before the trip" },',
    '{ ["do"] = "note", text = "Healer setup" },\n  { ["do"] = "note", text = "Sell before the trip" },',
)
L = login(A, "DruidKitDB = {}")
L.execute("DruidKit_StepDone(); DruidKit_StepsEvaluate()")
first = L.eval("DruidKitDB.routeStep")
# simulate the saved variables surviving a /reload into route b
saved = L.eval("DruidKitDB")
keys = [k for k in saved["doneKeys"].keys()] if saved["doneKeys"] else []  # noqa: SIM118 (lupa table)
db = (
    "DruidKitDB = { routeId = 'a', routeStep = 2, manual = {}, doneKeys = {"
    + ",".join(f'["{k}"] = true' for k in keys)
    + "} }"
)
L2 = login(B, db)
L2.execute("DruidKit_StepsEvaluate()")
r = L2.eval("DruidKitDB.routeStep")
m1 = L2.eval("DruidKitDB.manual[1]")
m2 = L2.eval("DruidKitDB.manual[2]")
print(first, keys, r, m1, m2)
check(first == 2, "Done ticks the sell step", first)
check("note|Sell before the trip#1" in keys, "the tick is remembered by kind and text", keys)
check(m2 is True and not m1, "new route: the same sell step is still done; a new step is not", (m1, m2))
check(r == 1, "the window shows the new, undone step first", r)

# A trip you already made: the quest step right after it is done, so the trip is done too.
C = """DruidKitRoute = { id = "c", sections = { { title = "Trip", steps = {
  { ["do"] = "fly", to = "Lakeshire", npc = "Dungar" },
  { ["do"] = "accept", q = 95772, name = "Songblade Search" },
  { ["do"] = "fly", to = "Menethil Harbor", npc = "Dungar" },
} } } }"""
L3 = login(C, "DruidKitDB = {}")
L3.execute('LOG[95772] = { title = "Songblade Search" }; ZONE = "Stormwind City"; DruidKit_StepsEvaluate()')
r3 = L3.eval("DruidKitDB.routeStep")
check(r3 == 3, "a flight whose next quest is already in the log counts as done (no going back to it)", r3)
done("keepticks_test")
