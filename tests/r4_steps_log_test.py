"""The step log gets every step once, whenever it is first finished: steps behind a catch-up, steps after an unskip,
and steps ticked by an event (flight map, trainer, vendor)."""

from lupa.lua51 import LuaRuntime

from expect import check, done
from wowenv import HERE, source

SRC = (HERE / "steps_test.py").read_text(encoding="utf-8")
OPEN = "L.execute(r" + '"' * 3
MOCKS = SRC.split(OPEN, 1)[1].split("DruidKitRoute = {")[0]
LOGGED = r"""
function logged(i) local n = 0 for _, l in ipairs(DruidKitDB.stepLog) do if l.i == i then n = n + 1 end end return n end
function entry(i) for _, l in ipairs(DruidKitDB.stepLog) do if l.i == i then return l end end end
"""


def setup(sections, extra=""):
    L = LuaRuntime(unpack_returned_tuples=True)
    L.execute(MOCKS)
    L.execute("COMBAT = false; function InCombatLockdown() return COMBAT end\n" + LOGGED + extra)
    L.execute("DruidKitRoute = { id = 'c', sections = {" + sections + "} }")
    L.execute(source("DruidKit/DruidKit_Steps.lua"))
    L.execute(r"""
for _, f in ipairs(frames) do if f.events and f.events.QUEST_DETAIL then ev = f end end
function fire(e, a) ev.on_OnEvent(ev, e, a) end
function cur() return DruidKitDB.routeStep end
""")
    return L, L.globals()


# Catch-up passes into a later section; the earlier section, started afterwards, is still logged.
L, g = setup(
    r"""
 { title = 'Deadmines', steps = { { ["do"] = "accept", q = 1, name = "One" }, { ["do"] = "complete", q = 1, name = "One" } } },
 { title = 'Dusk', steps = { { ["do"] = "accept", q = 5, name = "Five" }, { ["do"] = "turnin", q = 6, name = "Six" },
   { ["do"] = "note", text = "end" } } }""",
    "DONE[6] = true",
)
L.execute(r"""
fire("PLAYER_LOGIN")
CURQ = 1; CURTITLE = "One"; fire("QUEST_DETAIL")
DruidKitDB.cur.secs = 600
LOG[1].done = true; fire("QUEST_LOG_UPDATE")
""")
check(
    g.logged(1) == 1 and g.logged(2) == 1,
    "steps of an earlier section are logged after a catch-up in a later one",
    (g.logged(1), g.logged(2)),
)
check(g.entry(2) and g.entry(2).secs == 600, "with the time spent on them", g.entry(2) and g.entry(2).secs)
check(g.logged(3) == 1 and g.logged(4) == 1, "steps passed by the catch-up are logged once", (g.logged(3), g.logged(4)))

# Skip a quest, go on, unskip it: its hand-in, set aside while skipped, is logged when it's done.
L, g = setup(
    r"""
 { title = 'S', steps = {
  { ["do"] = "accept", q = 2, name = "Two" },
  { ["do"] = "complete", q = 2, name = "Two" },
  { ["do"] = "note", text = "a" },
  { ["do"] = "turnin", q = 2, name = "Two" },
  { ["do"] = "note", text = "b" },
  { ["do"] = "note", text = "end" } } }""",
    "LOG[2] = { title = 'Two' }",
)
L.execute(r"""
fire("PLAYER_LOGIN")
DruidKit_StepSkip(); DruidKit_StepDone(); DruidKit_StepDone()
DruidKit_StepsCommand("unskip")
LOG[2].done = true; fire("QUEST_LOG_UPDATE")
LOG[2] = nil; DONE[2] = true; fire("QUEST_LOG_UPDATE")
""")
check(g.cur() == 6, "the unskipped quest is handed in and the route moves on", g.cur())
check(g.logged(4) == 1, "its hand-in is logged once", g.logged(4))
check(
    g.logged(3) == 1 and g.logged(5) == 1,
    "steps ticked before the unskip aren't logged again",
    (g.logged(3), g.logged(5)),
)
check(g.logged(2) == 2, "the skipped step gets its skip and its real completion", g.logged(2))

# Skip at a step, unskip, finish it: its real completion is logged once beside the skip.
L, g = setup(
    r"""
 { title = 'S', steps = {
  { ["do"] = "accept", q = 2, name = "Two" },
  { ["do"] = "complete", q = 2, name = "Two" },
  { ["do"] = "note", text = "a" },
  { ["do"] = "note", text = "end" } } }""",
    "LOG[2] = { title = 'Two' }",
)
L.execute(r"""
fire("PLAYER_LOGIN")
DruidKit_StepSkip(); DruidKit_StepsCommand("unskip")
DruidKitDB.cur.secs = 300
LOG[2].done = true; fire("QUEST_LOG_UPDATE")
DruidKit_StepsCommand("reset"); DruidKit_StepSkip(); DruidKit_StepsCommand("unskip"); fire("QUEST_LOG_UPDATE")
hows = {}
for _, l in ipairs(DruidKitDB.stepLog) do if l.i == 2 then hows[#hows + 1] = l.how .. ":" .. l.secs end end
""")
hows = list(g.hows.values())
check(hows == ["skipped:0", "done:300"], "the unskipped step logs its completion with its time, once", hows)

# fp, train and "Sell ..." steps ticked by an event are logged with the time spent on them.
L, g = setup(
    r"""
 { title = 'S', steps = {
  { ["do"] = "fp", to = "Thelsamar", npc = "Thorgrum Borrelson" },
  { ["do"] = "train" },
  { ["do"] = "note", text = "Sell junk" },
  { ["do"] = "note", text = "end" } } }""",
    r"""
function NumTaxiNodes() return 1 end
function TaxiNodeGetType() return "CURRENT" end
function TaxiNodeName() return "Thelsamar, Loch Modan" end
function UnitName(u) return u == "npc" and "Kal" or "Cu" end
function DruidKit_IsDruidTrainer(n) return n == "Kal" end
""",
)
L.execute(r"""
fire("PLAYER_LOGIN"); DruidKitDB.cur.secs = 120
fire("TAXIMAP_OPENED"); DruidKitDB.cur.secs = 60
fire("TRAINER_SHOW"); fire("TRAINER_CLOSED"); DruidKitDB.cur.secs = 30
fire("MERCHANT_SHOW")
""")
check(g.cur() == 4, "the three steps tick", g.cur())
secs = [g.entry(i) and g.entry(i).secs for i in (1, 2, 3)]
check(secs == [120, 60, 30], "each is logged with its time on step", secs)
check(all(g.logged(i) == 1 for i in (1, 2, 3)), "once each", [g.logged(i) for i in (1, 2, 3)])

# A saved log from before DB.logged existed keeps its high-water mark: those steps aren't logged again.
L, g = setup(
    r"""
 { title = 'S', steps = { { ["do"] = "turnin", q = 1, name = "One" }, { ["do"] = "note", text = "end" } } }""",
    "DONE[1] = true; DruidKitDB = { routeId = 'c', routeStep = 1, loggedTo = 2, stepLog = {} }",
)
L.execute('fire("PLAYER_LOGIN")')
check(g.cur() == 2 and g.logged(1) == 0, "an old loggedTo is carried over", (g.cur(), g.logged(1)))

done("r4_steps_log_test")
