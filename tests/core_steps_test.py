"""Step tracker: fp/train ticks need the right NPC, rewinds don't flood the log, skipped quests aren't auto-accepted,
the Buff button hides after combat, bag lines follow Bags' rescans, and lore is kept for route quests only."""

from lupa.lua51 import LuaRuntime

from expect import check, done
from wowenv import HERE, source

SRC = (HERE / "steps_test.py").read_text(encoding="utf-8")
OPEN = "L.execute(r" + '"' * 3
MOCKS = SRC.split(OPEN, 1)[1].split("DruidKitRoute = {")[0]


def setup(route, extra=""):
    L = LuaRuntime(unpack_returned_tuples=True)
    L.execute(MOCKS)
    L.execute("COMBAT = false; function InCombatLockdown() return COMBAT end\n" + extra)
    L.execute("DruidKitRoute = { id = 'c', sections = { { title = 'S', steps = {" + route + "} } } }")
    L.execute(source("DruidKit/DruidKit_Steps.lua"))
    L.execute(r"""
for _, f in ipairs(frames) do if f.events and f.events.QUEST_DETAIL then ev = f end end
function fire(e, a) ev.on_OnEvent(ev, e, a) end
function cur() return DruidKitDB.routeStep end
""")
    return L, L.globals()


# 3: an fp step ticks only at its own flight master; a train step only at the trainer it names.
L, g = setup(
    r"""
  { ["do"] = "fp", to = "Thelsamar", npc = "Thorgrum Borrelson" },
  { ["do"] = "train", npc = "Loganaar (druid trainer)" },
  { ["do"] = "train" },
  { ["do"] = "note", text = "end" },
""",
    r"""
NODE = "Ironforge, Dun Morogh"
function NumTaxiNodes() return 1 end
function TaxiNodeGetType() return "CURRENT" end
function TaxiNodeName() return NODE end
NPC = "Kal"
function UnitName(u) return u == "npc" and NPC or "Cu" end
function DruidKit_IsDruidTrainer(n) return n == "Kal" or n == "Loganaar" end
""",
)
L.execute(r"""
fire("PLAYER_LOGIN")
R = {}
fire("TAXIMAP_OPENED"); R[1] = cur()
NODE = "Thelsamar, Loch Modan"; fire("TAXIMAP_OPENED"); R[2] = cur()
fire("TRAINER_SHOW"); fire("TRAINER_CLOSED"); R[3] = cur()
NPC = "Loganaar"; fire("TRAINER_SHOW"); fire("TRAINER_CLOSED"); R[4] = cur()
NPC = "Tannysa"; fire("TRAINER_SHOW"); fire("TRAINER_CLOSED"); R[5] = cur()
NPC = "Ilyenia Moonfire"; fire("TRAINER_SHOW"); fire("TRAINER_CLOSED"); R[6] = cur()
NPC = "Kal"; fire("TRAINER_SHOW"); fire("TRAINER_CLOSED"); R[7] = cur()
""")
r = list(g.R.values())
check(r[0] == 1, "another flight master doesn't tick the fp step", r[0])
check(r[1] == 2, "the step's own flight master ticks it", r[1])
check(r[2] == 2 and r[3] == 3, "a train step waits for the trainer it names", r[2:4])
check(r[4] == 3 and r[5] == 3, "a profession trainer or weapon master doesn't tick a train step", r[4:6])
check(r[6] == 4, "a druid trainer ticks a train step that names none", r[6])

# 4: rewinding (/dk steps reset, unskip) doesn't log every step walked past again.
L, g = setup(
    r"""
  { ["do"] = "turnin", q = 1, name = "One" },
  { ["do"] = "turnin", q = 2, name = "Two" },
  { ["do"] = "turnin", q = 3, name = "Three" },
  { ["do"] = "accept", q = 4, name = "Four" },
""",
    "DONE[1] = true; DONE[2] = true; DONE[3] = true",
)
L.execute(r"""
fire("PLAYER_LOGIN")
n0 = #DruidKitDB.stepLog
DruidKit_StepsCommand("reset"); n1 = #DruidKitDB.stepLog
DruidKit_StepsCommand("unskip"); n2 = #DruidKitDB.stepLog
""")
check(g.n0 == 3 and g.cur() == 4, "steps done at login are logged once", (g.n0, g.cur()))
check(g.n1 == 3 and g.n2 == 3, "reset and unskip don't log them again", (g.n1, g.n2))

LOGGED = r"""
function logged(i) local n = 0 for _, l in ipairs(DruidKitDB.stepLog) do if l.i == i then n = n + 1 end end return n end
"""
# unskip stops on a step that isn't done; accepting it later must not log the done steps after it again.
L, g = setup(
    r"""
  { ["do"] = "turnin", q = 1, name = "One" },
  { ["do"] = "accept", q = 2, name = "Two" },
  { ["do"] = "complete", q = 3, name = "Three" },
  { ["do"] = "note", text = "end" },
""",
    "DONE[1] = true; DONE[3] = true" + LOGGED,
)
L.execute(r"""
fire("PLAYER_LOGIN")
DruidKit_StepSkip(); a = cur()
DruidKit_StepsCommand("unskip"); b = cur()
CURQ = 2; CURTITLE = "Two"; fire("QUEST_DETAIL")
""")
check(
    g.a == 4 and g.b == 2 and g.cur() == 4, "unskip goes back to the quest, accepting it moves on", (g.a, g.b, g.cur())
)
check(
    g.logged(1) == 1 and g.logged(3) == 1,
    "steps after the unskipped quest aren't logged twice",
    (g.logged(1), g.logged(3)),
)

# reset stops on a hand-ticked step; Done on it must not log it or the steps after it again.
L, g = setup(
    r"""
  { ["do"] = "turnin", q = 1, name = "One" },
  { ["do"] = "note", text = "Hand" },
  { ["do"] = "complete", q = 3, name = "Three" },
  { ["do"] = "note", text = "end" },
""",
    "DONE[1] = true; DONE[3] = true" + LOGGED,
)
L.execute(r"""
fire("PLAYER_LOGIN"); a = cur()
DruidKit_StepDone()
DruidKit_StepsCommand("reset"); b = cur()
DruidKit_StepDone()
""")
check(g.a == 2 and g.b == 2 and g.cur() == 4, "reset stops at the hand-ticked step", (g.a, g.b, g.cur()))
check(g.logged(2) == 1 and g.logged(3) == 1, "Done after a reset doesn't log steps again", (g.logged(2), g.logged(3)))

# 6: skipped and passed quests aren't auto-accepted.
L, g = setup(r"""
  { ["do"] = "accept", q = 10, name = "Ten" },
  { ["do"] = "accept", q = 11, name = "Eleven" },
  { ["do"] = "accept", q = 12, name = "Twelve" },
""")
L.execute(r"""
fire("PLAYER_LOGIN")
DruidKit_StepSkip()
CURQ = 10; CURTITLE = "Ten"; fire("QUEST_DETAIL"); R1 = ACCEPTED
DruidKitDB.passedQ[11] = true
CURQ = 11; CURTITLE = "Eleven"; fire("QUEST_DETAIL"); R2 = ACCEPTED
CURQ = 12; CURTITLE = "Twelve"; fire("QUEST_DETAIL"); R3 = ACCEPTED
""")
check(g.R1 is None and g.R2 is None, "skipped and passed quests are left for you", (g.R1, g.R2))
check(g.R3 == 12, "other route quests are still accepted", g.R3)

# 5: the Buff button hidden in combat is really hidden once combat ends.
L, g = setup(r"""{ ["do"] = "complete", q = 20, name = "Kill", party = true },""")
L.execute(r"""
fire("PLAYER_LOGIN")
b = DruidKitBuffButton
COMBAT = true; DruidKit_ToggleSteps(false); inCombat = b.shown
COMBAT = false; fire("PLAYER_REGEN_ENABLED")
""")
check(g.inCombat is True and g.b.shown is False, "Buff button hides after combat", (g.inCombat, g.b.shown))

# 7: bag lines follow Bags' own rescan, even when it lands after the step window's bag update. Quest log
# selection is put back.
L, g = setup(
    r"""{ ["do"] = "complete", q = 30, name = "Banner", party = true, freeBags = 2 },""",
    r"""
STARTERS = {}
DruidKit_QuestStarters = function() return STARTERS end
LOG[30] = { title = "Banner" }
SEL = 0
function GetQuestLogSelection() return SEL end
function SelectQuestLogEntry(i) SEL = i end
function GetQuestLogQuestText() return "desc", "Raise the banner." end
""",
)
L.execute(r"""
fire("PLAYER_LOGIN")
fire("BAG_UPDATE_DELAYED")
STARTERS = { { name = "Dusty Note" } }
ev.on_OnUpdate(ev, 2.1)
detail = DruidKitSteps.detail.text
""")
check("QUEST TO START in your bags: Dusty Note" in g.detail, "a starter looted shows once Bags rescans", g.detail)
check("Quest says: Raise the banner" in g.detail and g.SEL == 0, "quest text read, log selection put back", g.SEL)

# 8: lore is kept for route quests only; others are pruned on load.
L, g = setup(
    r"""{ ["do"] = "accept", q = 150, name = "Murloc Poachers" },""",
    r"""
DruidKitDB = { lore = { [150] = { text = "keep" }, [999] = { text = "old" } } }
function GetQuestText() return "Some story." end
""",
)
L.execute(r"""
fire("PLAYER_LOGIN")
CURQ = 777; CURTITLE = "Not ours"; fire("QUEST_DETAIL")
""")
lore = g.DruidKitDB.lore
check(lore[150] is not None and lore[999] is None, "lore for quests off the route is pruned on load", list(lore.keys()))
check(lore[777] is None, "a quest off the route isn't kept", lore[777])
done("core_steps_test")
