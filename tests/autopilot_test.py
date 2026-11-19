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
