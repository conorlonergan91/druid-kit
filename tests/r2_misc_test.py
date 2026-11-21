"""Auto hand-in leaves skipped quests alone; Bank check's Store/Take re-check the slot before moving; the tracker's
gold line uses the same per-level mount target as Bag check."""

from lupa.lua51 import LuaRuntime

from expect import check, done
from wowenv import HERE, runtime, source

# 1. A skipped quest is not handed in for you.
SRC = (HERE / "steps_test.py").read_text(encoding="utf-8")
OPEN = "L.execute(r" + '"' * 3
MOCKS = SRC.split(OPEN, 1)[1].split("DruidKitRoute = {")[0]
L = LuaRuntime(unpack_returned_tuples=True)
L.execute(MOCKS)
L.execute(r"""
LOG = { [89] = { title = "The Everstill Bridge" } }
DruidKitRoute = { id = "hs", sections = { { title = "S", steps = {
  { ["do"] = "complete", q = 89, name = "The Everstill Bridge" },
  { ["do"] = "note", text = "later" },
  { ["do"] = "turnin", q = 89, name = "The Everstill Bridge" },
} } } }
DruidKitDB = {}
DruidKit_RewardPick = function(n) return 2, "best upgrade for you" end
""")
L.execute(source("DruidKit/DruidKit_Steps.lua"))
L.execute(r"""
for _, f in ipairs(frames) do if f.events and f.events.QUEST_DETAIL then ev = f end end
ev.on_OnEvent(ev, "PLAYER_LOGIN")
DruidKit_StepSkip()
CURQ = 89; CURTITLE = "The Everstill Bridge"; CHOICES = { "Axe", "Robe" }
ev.on_OnEvent(ev, "QUEST_PROGRESS"); ev.on_OnEvent(ev, "QUEST_COMPLETE")
""")
g = L.globals()
check(g.COMPLETED is None and g.REWARD is None, "a skipped quest isn't handed in for you", (g.COMPLETED, g.REWARD))

# 2. Bank check: Store refuses when the slot now holds something else.
B = runtime("ui")
B.execute(r"""
UISpecialFrames = {}
function GetTime() return 100 end
ITEMS.book = {"Venomous Journeys","book",1,1,0,"","",1,"",1,0,12,0,4}
BAG[0] = { "book" }
BAG[-1] = {}
C_Container.GetContainerNumSlots = function(b) if b == 0 then return 1 elseif b == -1 then return 2 end return 0 end
MOVED = {}
C_Container.UseContainerItem = function(b, s) MOVED[#MOVED + 1] = BAG[b][s] end
BankFrame = { IsShown = function() return false end }
""")
B.execute(source("DruidKit/DruidKit_Style.lua"))
B.execute(source("DruidKit/DruidKit_Bags.lua"))
B.execute(source("DruidKit/DruidKit_Bank.lua"))
B.execute(r"""
for _, f in ipairs(frames) do if f.on_OnEvent then f.on_OnEvent(f, "PLAYER_LOGIN") end end
for _, f in ipairs(frames) do if f.on_OnEvent then f.on_OnEvent(f, "BANKFRAME_OPENED") end end
BAG[0][1] = "robe"
for _, f in ipairs(frames) do if f.text == "Store" and f.on_OnClick then f.on_OnClick(f) break end end
""")
check(
    len(B.globals().MOVED) == 0,
    "Store doesn't move a different item now in that slot",
    list(B.globals().MOVED.values()),
)
B.execute(r"""
BAG[0][1] = "book"
for _, f in ipairs(frames) do if f.on_OnEvent then f.on_OnEvent(f, "BAG_UPDATE_DELAYED") end end
for _, f in ipairs(frames) do if f.text == "Store" and f.on_OnClick then f.on_OnClick(f) break end end
""")
check(
    list(B.globals().MOVED.values()) == ["book"],
    "with the same item back, Store moves it",
    list(B.globals().MOVED.values()),
)

# 3. Tracker gold line: Bag check's per-level target (DruidKit_MountTarget), not a separate one.
H = (HERE / "helpers_test.py").read_text(encoding="utf-8")
HMOCKS = H.split(OPEN, 1)[1].split('""")', 1)[0]
bags = source("DruidKit/DruidKit_Bags.lua")
target_fn = bags[bags.index("local MOUNT_GOLD") : bags.index("local function mountLine")]
T = LuaRuntime(unpack_returned_tuples=True)
T.execute(HMOCKS)
T.execute(target_fn + "\nDruidKit_MountTarget = mountTarget")
T.execute(source("DruidKit/DruidKit_Helpers.lua"))
T.execute("LVL = 30; function GetMoney() return 100000 end; line = DruidKit_GoldLine(); aim = DruidKit_MountTarget(30)")
line, aim = T.globals().line or "", T.globals().aim
check(f"aim {aim // 10000}g at 30" in line, "gold line aims for Bag check's level-30 target", (line, aim))
done("r2_misc_test")
