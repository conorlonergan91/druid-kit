"""Vendor autopilot: sells junk and unusable gear, keeps quest items and upgrades, repairs, says the mount money line;
loot alerts also fire for valuable white items; /dk autosell off stops it."""
from wowenv import runtime, source
from expect import check, done

def run(extra=""):
    L = runtime("ui")
    L.execute("UISpecialFrames={}")
    L.execute(source("DruidKit/DruidKit_Style.lua"))
    L.execute(r"""
MONEY = 35000; REPAIRED = false
function GetMoney() return MONEY end
function CanMerchantRepair() return true end
function GetRepairAllCost() return 4500, true end
function RepairAllItems() REPAIRED = true; MONEY = MONEY - 4500 end
SOLD = {}
C_Container.UseContainerItem = function(b, s) SOLD[#SOLD+1] = BAG[b][s]; BAG[b][s] = nil end
DruidKitDB = DruidKitDB or {}
""" + extra)
    L.execute(source("DruidKit/DruidKit_Bags.lua"))
    L.execute('MerchantFrame = CreateFrame("Frame"); MerchantFrame.IsShown = function() return true end')
    return L

L = run()
L.execute(r"""
ev=frames[1]; ev.on_OnEvent(ev,"PLAYER_LOGIN")
ev.on_OnEvent(ev, "MERCHANT_SHOW")
""")
g = L.globals()
sold = list(g.SOLD.values())
said = list(g.printed.values())
print(sold, said[-4:])
check("grey" in sold, "grey junk sold", sold)
check("mail" in sold, "gear druids can't use sold", sold)
check("note" not in sold and "robe" not in sold, "quest item and upgrade kept", sold)
check("herb" not in sold, "herbs kept", sold)
check(g.REPAIRED is True, "repaired", g.REPAIRED)
check(any("Mount money" in p for p in said), "mount money line after selling", said[-2:])
check(any("Buyback" in p for p in said), "says how to undo", "")
log = L.globals().DruidKitDB.soldLog
check(log is not None and len(list(log.values())) == 3, "every autopilot sale is logged for the update", log and len(list(log.values())))

# Cooked food (Well Fed) and cooking meat are never sold by the autopilot (19 Nov: it sold Redridge Goulash).
L = run(r"""
ITEMS.goulash = {"Redridge Goulash","goulash",1,15,10,"","",20,"",1,40,0,5}
ITEMS.spidermeat = {"Crisp Spider Meat","spidermeat",1,10,0,"","",10,"",1,8,7,8}
ITEMS.mutton = {"Mutton Chop","mutton",1,15,5,"","",20,"",1,25,0,5}
ITEMS.bread = {"Old Bread","bread",1,5,1,"","",20,"",1,1,0,5}
C_TooltipInfo = { GetHyperlink = function(l)
  if l == "goulash" then return { lines = { { leftText = "Use: Restores health. If you spend at least 10 seconds eating you will become well fed." } } } end
  return { lines = {} } end }
BAG[0][8] = "goulash"; BAG[0][9] = "spidermeat"; BAG[0][10] = "bread"
C_Container.GetContainerNumSlots = function(b) return b == 0 and 10 or 0 end
DruidKit_NeededFor = function(name) return nil, true, false end
""")
L.execute(r"""
ev=frames[1]; ev.on_OnEvent(ev,"PLAYER_LOGIN"); ev.on_OnEvent(ev, "MERCHANT_SHOW")
""")
sold2 = list(L.globals().SOLD.values())
print("sold2", sold2)
check("goulash" not in sold2, "cooked Well Fed food is never auto-sold", sold2)
check("spidermeat" in sold2, "materials no recipe of yours uses are sold (player OK, 19 Nov)", sold2)
check("bread" not in sold2, "no food is auto-sold (it stays a suggestion in Alt+B)", sold2)

# A recipe in your bags keeps its materials; extra consumables and worse bandages are sold; Buff picks an elixir.
L = run(r"""
ITEMS.spidermeat = {"Crisp Spider Meat","spidermeat",1,10,0,"","",10,"",1,8,7,8}
ITEMS.recipe = {"Recipe: Redridge Goulash","recipe",1,20,0,"","",1,"",1,50,9,5}
ITEMS.elix1 = {"Elixir of Minor Strength","elix1",1,5,2,"","",20,"",1,10,0,2}
ITEMS.elix2 = {"Elixir of Minor Strength","elix2",1,5,2,"","",20,"",1,10,0,2}
ITEMS.band1 = {"Heavy Linen Bandage","band1",1,10,0,"","",20,"",1,20,0,7}
ITEMS.band2 = {"Wool Bandage","band2",1,20,0,"","",20,"",1,30,0,7}
COUNTS = { elix1 = 8, elix2 = 2, band1 = 20, band2 = 31 }
local gi = C_Container.GetContainerItemInfo
C_Container.GetContainerItemInfo = function(b, s) local r = gi(b, s); if r and COUNTS[r.hyperlink] then r.stackCount = COUNTS[r.hyperlink] end return r end
C_TooltipInfo = { GetHyperlink = function(l)
  if l == "recipe" then return { lines = { { leftText = "Requires Crisp Spider Meat (1)" } } } end
  return { lines = {} } end }
function GetItemSpell(l) if l == "elix1" or l == "elix2" then return "Lesser Strength" end end
C_UnitAuras = { GetAuraDataBySpellName = function() return nil end }
BAG[0][8] = "spidermeat"; BAG[0][9] = "recipe"; BAG[0][10] = "elix1"; BAG[0][11] = "elix2"; BAG[0][12] = "band1"; BAG[0][13] = "band2"
C_Container.GetContainerNumSlots = function(b) return b == 0 and 13 or 0 end
DruidKit_NeededFor = function(name) return nil, true, false end
""")
L.execute(r"""
ev=frames[1]; ev.on_OnEvent(ev,"PLAYER_LOGIN")
buff = DruidKit_NextBuff()
buffName = buff and buff.name
ev.on_OnEvent(ev, "MERCHANT_SHOW")
""")
g = L.globals()
sold3 = list(g.SOLD.values())
print("sold3", sold3, g.buffName)
check("spidermeat" not in sold3, "materials a recipe in your bags needs are kept", sold3)
check("elix2" in sold3 and "elix1" not in sold3, "extra elixirs sold, a stock of 8 kept", sold3)
check("band1" in sold3 and "band2" not in sold3, "worse bandage sold, best kept", sold3)
check(g.buffName == "Elixir of Minor Strength", "Buff picks an elixir you don't have active", g.buffName)

# Classic data: an elixir filed under subclass 0 still counts (Buff, extras); a red Durability line is not "can't use".
L = run(r"""
ITEMS.elix0 = {"Elixir of Minor Defense","elix0",1,5,1,"","",20,"",1,10,0,0}
ITEMS.broken = {"Worn Leather Boots","broken",2,15,10,"","",1,"INVTYPE_FEET",1,300,4,2,2}
STATS.broken = {RESISTANCE0_NAME=10}
function GetItemSpell(l) if l == "elix0" then return "Lesser Armor" end end
C_UnitAuras = { GetAuraDataBySpellName = function() return nil end }
C_TooltipInfo = { GetHyperlink = function(l)
  if l == "broken" then return { lines = { { leftText = "Durability 0 / 30", leftColor = { r = 1, g = 0.13, b = 0.13 } } } } end
  return { lines = {} } end }
BAG[0][8] = "elix0"; BAG[0][9] = "broken"
C_Container.GetContainerNumSlots = function(b) return b == 0 and 9 or 0 end
""")
L.execute(r"""
nb = DruidKit_NextBuff(); nbName = nb and nb.name
cw = DruidKit_CantWield("broken")
""")
g = L.globals()
check(g.nbName == "Elixir of Minor Defense", "an elixir filed under subclass 0 is found by Buff", g.nbName)
check(g.cw is None, "a red Durability line doesn't make gear unusable", g.cw)

L = run("DruidKitDB = { autoSell = false }")
L.execute(r"""
ev=frames[1]; ev.on_OnEvent(ev,"PLAYER_LOGIN"); ev.on_OnEvent(ev, "MERCHANT_SHOW")
""")
check(len(list(L.globals().SOLD.values())) == 0, "/dk autosell off: nothing sold", list(L.globals().SOLD.values()))

L = run()
L.execute(r"""
function UnitLevel() return 30 end
MONEY = 100000
line = DruidKit_MountLine()
t30 = DruidKit_MountTarget(30); t40 = DruidKit_MountTarget(40)
""")
g = L.globals()
check("BEHIND" in g.line, "mount line says BEHIND with a gap", g.line)
check(g.t40 == 1000000 and 300000 < g.t30 < 400000, "target 100g at 40, ~35g at 30", (g.t30, g.t40))
done("autopilot_test")
