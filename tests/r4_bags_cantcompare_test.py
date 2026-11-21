"""Gear it can't compare (idols, on-use trinkets, an off-hand while you wield a two-hander) is never judged for you:
no automatic roll, no automatic quest reward pick, and the loot helper says take it."""

from lupa.lua51 import LuaRuntime

from expect import check, done
from wowenv import HERE, runtime, source

SETUP = r"""
UISpecialFrames = {}
function GetMoney() return 0 end
DruidKitDB = {}
ITEMS.idol = {"Idol of Something","idol",3,30,10,"","",1,"INVTYPE_RELIC",1,500,4,8,1}
ITEMS.trink = {"Shiny Trinket","trink",2,30,10,"","",1,"INVTYPE_TRINKET",1,400,4,0,1}
ITEMS.oh = {"Great Orb","oh",1,15,10,"","",1,"INVTYPE_HOLDABLE",1,300,4,0,1}
ITEMS.hidol = {"Idol of Later","hidol",3,40,30,"","",1,"INVTYPE_RELIC",1,500,4,8,1}
ITEMS.htrink = {"Far Trinket","htrink",2,40,30,"","",1,"INVTYPE_TRINKET",1,400,4,0,1}
ITEMS.staff = {"Old Staff","staff",1,10,5,"","",1,"INVTYPE_2HWEAPON",1,100,2,10,1}
ITEMS.cloak = {"Plain Cloak","cloak",1,10,5,"","",1,"INVTYPE_CLOAK",1,50,4,1,1}
STATS.staff = {ITEM_MOD_STAMINA_SHORT=2}
STATS.oh = {ITEM_MOD_STAMINA_SHORT=8, ITEM_MOD_INTELLECT_SHORT=8}
STATS.cloak = {ITEM_MOD_STAMINA_SHORT=3}
EQ[16] = "staff"
"""


def fresh(extra=""):
    L = runtime("ui")
    L.execute(SETUP + extra)
    L.execute(source("DruidKit/DruidKit_Style.lua"))
    L.execute(source("DruidKit/DruidKit_Bags.lua"))
    L.execute("frames[1].on_OnEvent(frames[1], 'PLAYER_LOGIN')")
    return L


# Loot rolls: no automatic Greed (and no bind-on-pickup confirm); the window asks you.
L = fresh(r"""
ROLLED = {}
function RollOnLoot(id, c) ROLLED[#ROLLED+1] = id end
function ConfirmLootRoll(id) ROLLED[#ROLLED+1] = "confirm" end
ROLL = { "idol", "trink", "oh", "hidol", "htrink" }
function GetLootRollItemLink(id) return LINK(ROLL[id]) end
function GetLootRollItemInfo(id) return 1, ITEMS[ROLL[id]][1], 1, 3, true, true, true end
""")
L.execute(r"""
function fire(e, a) for _, f in ipairs(frames) do if f.on_OnEvent then f.on_OnEvent(f, e, a) end end end
ADV = {}
for id = 1, 5 do
  local a, why, pick, auto = DruidKitBagsAPI.rollAdvice(LINK(ROLL[id]), true, true)
  ADV[id] = a .. " | " .. why .. " | " .. tostring(pick) .. " | " .. tostring(auto)
  fire("START_LOOT_ROLL", id); fire("CONFIRM_LOOT_ROLL", id)
end
rows = {} for _, f in ipairs(allfs) do if f.text ~= "" then rows[#rows+1] = f.text end end
""")
g = L.globals()
adv = list(g.ADV.values())
check(
    all(a.startswith("YOUR CALL | can't compare") for a in adv),
    "idol, trinket (also far above your level), off-hand vs 2H: your call",
    adv,
)
check(all(a.endswith("nil | nil") for a in adv), "no advised button and no automatic roll", adv)
check(len(list(g.ROLLED.values())) == 0, "nothing rolled or confirmed for you", list(g.ROLLED.values()))
check(any("Idol of Something" in r for r in g.rows.values()), "the roll window shows it", list(g.rows.values()))

# Quest rewards: a choice it can't compare means you pick (no "sells for the most").
L = fresh(r"""
CHOICES = { "cloak", "idol" }
function GetQuestItemLink(_, i) return LINK(CHOICES[i]) end
""")
L.execute("i, why = DruidKit_RewardPick(2)")
g = L.globals()
check(
    g.i is None and g.why == "can't compare Idol of Something",
    "a reward choice it can't compare: no pick, the player picks",
    (g.i, g.why),
)
L.execute("CHOICES = { 'cloak', 'staff' }; i2 = DruidKit_RewardPick(2)")
check(L.globals().i2 is not None, "comparable rewards are still picked", L.globals().i2)

# Loot helper with full bags: take it, can't compare.
L = fresh(r"""
function UnitLevel() return 20 end
function GetTime() return 100 end
LOOT = { { name = "Idol of Something", link = "idol" }, { name = "Idol of Later", link = "hidol" } }
function GetNumLootItems() return #LOOT end
function GetLootSlotType() return 1 end
function GetLootSlotInfo(i) local l = LOOT[i]; if l then return 1, l.name, 1, nil, 3, nil, false end end
function GetLootSlotLink(i) return LOOT[i] and LINK(LOOT[i].link) end
""")
L.execute(r"""
for _, f in ipairs(frames) do if f.on_OnEvent then f.on_OnEvent(f, "LOOT_OPENED") end end
rows = {} for _, f in ipairs(allfs) do if f.text ~= "" then rows[#rows+1] = f.text end end
""")
text = "\n".join(L.globals().rows.values())
check(
    "TAKE|r  Idol of Something" in text
    and "TAKE|r  Idol of Later" in text
    and text.count("can't compare: no stats") == 2,
    "loot helper: take, can't compare (also far above your level)",
    text,
)
# Auto hand-in with such a choice: nothing taken, and it says which item to judge.
SRC = (HERE / "steps_test.py").read_text(encoding="utf-8")
S = LuaRuntime(unpack_returned_tuples=True)
S.execute(SRC.split("L.execute(r" + '"' * 3, 1)[1].split("DruidKitRoute = {")[0])
S.execute(r"""
DruidKitRoute = { id = "r", sections = { { title = "S", steps = { { ["do"] = "turnin", q = 7, name = "Seven" } } } } }
DruidKitDB = {}
DruidKit_RewardPick = function(n) return nil, "can't compare Idol of Something" end
""")
S.execute(source("DruidKit/DruidKit_Steps.lua"))
S.execute(r"""
for _, f in ipairs(frames) do if f.events and f.events.QUEST_DETAIL then ev = f end end
ev.on_OnEvent(ev, "PLAYER_LOGIN")
LOG[7] = { title = "Seven", done = true }; CURQ = 7; CURTITLE = "Seven"; CHOICES = { "Plain Cloak", "Idol of Something" }
printed = {}; ev.on_OnEvent(ev, "QUEST_COMPLETE")
""")
said = list(S.globals().printed.values())
check(
    S.globals().REWARD is None
    and any(p.endswith("pick your reward yourself: can't compare Idol of Something.") for p in said),
    "quest hand-in: no reward taken, says which item you judge",
    said,
)
done("r4_bags_cantcompare_test")
