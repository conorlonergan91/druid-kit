"""Step tracker: fp/train ticks need the right NPC, rewinds don't flood the log, skipped quests aren't auto-accepted,
the Buff button hides after combat, the 2-second redraw doesn't rescan bags, and lore is kept for route quests only."""

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
NPC = "Kal"; TRADE = false
function UnitName(u) return u == "npc" and NPC or "Cu" end
function IsTradeskillTrainer() return TRADE end
""",
)
L.execute(r"""
fire("PLAYER_LOGIN")
R = {}
fire("TAXIMAP_OPENED"); R[1] = cur()
NODE = "Thelsamar, Loch Modan"; fire("TAXIMAP_OPENED"); R[2] = cur()
fire("TRAINER_SHOW"); fire("TRAINER_CLOSED"); R[3] = cur()
NPC = "Loganaar"; fire("TRAINER_SHOW"); fire("TRAINER_CLOSED"); R[4] = cur()
NPC = "Tannysa"; TRADE = true; fire("TRAINER_SHOW"); fire("TRAINER_CLOSED"); R[5] = cur()
TRADE = false; fire("TRAINER_SHOW"); fire("TRAINER_CLOSED"); R[6] = cur()
""")
r = list(g.R.values())
check(r[0] == 1, "another flight master doesn't tick the fp step", r[0])
check(r[1] == 2, "the step's own flight master ticks it", r[1])
check(r[2] == 2 and r[3] == 3, "a train step waits for the trainer it names", r[2:4])
check(r[4] == 3 and r[5] == 4, "a train step with no NPC needs a class trainer, not a profession trainer", r[4:6])

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

# 7: the 2-second redraw doesn't rescan bags; a bag update does. Quest log selection is put back.
L, g = setup(
    r"""{ ["do"] = "complete", q = 30, name = "Banner", party = true, freeBags = 2 },""",
    r"""
SCANS = 0
DruidKit_NextBuff = function() SCANS = SCANS + 1; return { name = "Elixir", count = 1 } end
DruidKit_SellCount = function() SCANS = SCANS + 1; return 0 end
LOG[30] = { title = "Banner" }
SEL = 0
function GetQuestLogSelection() return SEL end
function SelectQuestLogEntry(i) SEL = i end
function GetQuestLogQuestText() return "desc", "Raise the banner." end
""",
)
L.execute(r"""
fire("PLAYER_LOGIN")
s0 = SCANS
for i = 1, 5 do ev.on_OnUpdate(ev, 2.1) end
s1 = SCANS
fire("BAG_UPDATE_DELAYED")
s2 = SCANS
detail = DruidKitSteps.detail.text
""")
check(g.s0 > 0 and g.s1 == g.s0, "the timed redraw reuses bag lines", (g.s0, g.s1))
check(g.s2 > g.s1, "a bag update refreshes them", g.s2)
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
