"""Step window lines stay current on the 2-second redraw: quest text after Back, the Buff offer after an aura,
the sell count after Bags rescans, and the vendor distance while you walk."""

from lupa.lua51 import LuaRuntime

from expect import check, done
from wowenv import HERE, source

MOCKS = (HERE / "steps_test.py").read_text(encoding="utf-8").split('L.execute(r"""', 1)[1].split("DruidKitRoute = {")[0]


def setup(route, extra=""):
    L = LuaRuntime(unpack_returned_tuples=True)
    L.execute(MOCKS + "function InCombatLockdown() return false end\n" + extra)
    L.execute("DruidKitRoute = { id = 'c', sections = { { title = 'S', steps = {" + route + "} } } }")
    L.execute(source("DruidKit/DruidKit_Steps.lua"))
    L.execute(r"""
for _, f in ipairs(frames) do if f.events and f.events.QUEST_DETAIL then ev = f end end
function fire(e, a) ev.on_OnEvent(ev, e, a) end
""")
    return L, L.globals()


# Back shows the earlier step's own quest text.
L, g = setup(
    r"""
  { ["do"] = "complete", q = 40, name = "Forty" },
  { ["do"] = "complete", q = 41, name = "FortyOne" },
""",
    r"""
LOG[40] = { title = "Forty", done = true }; LOG[41] = { title = "FortyOne" }
SEL = 0
function GetQuestLogSelection() return SEL end
function SelectQuestLogEntry(i) SEL = i end
function GetQuestLogQuestText() return "desc", "Text of " .. CURLOG end
C_QuestLog.GetLogIndexForQuestID = function(q) CURLOG = q; return LOG[q] and 1 or nil end
""",
)
L.execute(r"""
fire("PLAYER_LOGIN"); a = DruidKitSteps.detail.text
DruidKit_StepBack(); b = DruidKitSteps.detail.text
""")
check("Quest says: Text of 41" in g.a, "the current step's quest text", g.a)
check("Quest says: Text of 40" in g.b, "Back shows the earlier step's quest text", g.b)

# The Buff offer goes once the buff is on you; the sell count follows Bags' rescan.
L, g = setup(
    r"""
  { ["do"] = "complete", q = 30, name = "Banner", party = true },
  { ["do"] = "note", text = "Sell junk" },
""",
    r"""
BUFF = { name = "Elixir", count = 1 }
DruidKit_NextBuff = function() return BUFF end
SELL = 0
DruidKit_SellCount = function() return SELL end
LOG[30] = { title = "Banner" }
""",
)
L.execute(r"""
fire("PLAYER_LOGIN"); a = DruidKitSteps.detail.text
BUFF = nil; ev.on_OnUpdate(ev, 2.1); b = DruidKitSteps.detail.text
LOG[30].done = true; fire("QUEST_LOG_UPDATE")
fire("BAG_UPDATE_DELAYED"); SELL = 3; ev.on_OnUpdate(ev, 2.1); c = DruidKitSteps.detail.text
""")
check("Hard fight" in g.a and "Hard fight" not in g.b, "the Buff offer goes once the buff is on", g.b)
check("3 items to sell" in g.c, "the sell count follows Bags' rescan", g.c)

# The nearest vendor's distance follows you.
L, g = setup(
    r"""{ ["do"] = "note", text = "Walk" },""",
    r"""
function GetContainerNumFreeSlots() return 0 end
DruidKitVendors = { { "Westfall", 50, 50, "Bob", "", false } }
PX = 0.4
C_Map = { GetBestMapForUnit = function() return 1 end,
  GetPlayerMapPosition = function() return { GetXY = function() return PX, 0.5 end } end }
DruidKit_FindMap = function() return 1 end
""",
)
L.execute(r"""
fire("PLAYER_LOGIN"); a = DruidKitSteps.detail.text
PX = 0.45; ev.on_OnUpdate(ev, 2.1); b = DruidKitSteps.detail.text
""")
check("Bob, 100 yards" in g.a and "Bob, 50 yards" in g.b, "vendor distance updates while walking", (g.a, g.b))
done("r3_steps_cache_test")
