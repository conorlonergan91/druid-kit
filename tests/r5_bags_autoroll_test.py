"""Automatic Greed is opt-in: off for new and old saves (autoRoll nil), `/dk autoroll on|off` toggles it, a bare
`/dk autoroll` says the state and how to change it. The roll window still advises when off; Need is never rolled."""

from expect import check, done
from wowenv import runtime, source

SETUP = r"""
UISpecialFrames = {}
function GetMoney() return 0 end
ITEMS.cloth = {"Linen Cloth","cloth",1,5,0,"","",20,"",1,15,7,5,0}
ITEMS.cloak = {"Fine Cloak","cloak",2,20,10,"","",1,"INVTYPE_CLOAK",1,50,4,1,2}
STATS.cloak = {ITEM_MOD_STAMINA_SHORT=9, ITEM_MOD_AGILITY_SHORT=9}
ROLLED = {}
function RollOnLoot(id, c) ROLLED[#ROLLED+1] = id .. ":" .. c end
ROLL = { "cloth", "cloak" }
function GetLootRollItemLink(id) return LINK(ROLL[id]) end
function GetLootRollItemInfo(id) return 1, ITEMS[ROLL[id]][1], 1, 2, true, true, true end
function fire(e, a) for _, f in ipairs(frames) do if f.on_OnEvent then f.on_OnEvent(f, e, a) end end end
function shown() local t = {} for _, f in ipairs(allfs) do if f.text ~= "" then t[#t+1] = f.text end end return table.concat(t, "\n") end
"""


def fresh(db):
    L = runtime("ui")
    L.execute(SETUP + "DruidKitDB = " + db)
    L.execute(source("DruidKit/DruidKit_Style.lua"))
    L.execute(source("DruidKit/DruidKit_Bags.lua"))
    L.execute("frames[1].on_OnEvent(frames[1], 'PLAYER_LOGIN')")
    return L


def rolled(L):
    return list(L.globals().ROLLED.values())


L = fresh("{}")
L.execute("printed = {}; fire('START_LOOT_ROLL', 1)")
check(rolled(L) == [], "an old or new save (autoRoll nil): no automatic Greed", rolled(L))
check("Linen Cloth" in L.eval("shown()"), "the roll window still shows the advice", L.eval("shown()"))

L.execute("printed = {}; DruidKit_HelperCommand('autoroll', '')")
said = "\n".join(L.globals().printed.values())
check(
    ": off" in said and "/dk autoroll on" in said and L.globals().DruidKitDB.autoRoll is None,
    "bare /dk autoroll: says off and how to turn it on, changes nothing",
    said,
)

L.execute(
    "DruidKit_HelperCommand('autoroll', 'on'); printed = {}; fire('START_LOOT_ROLL', 1); fire('START_LOOT_ROLL', 2)"
)
said = "\n".join(L.globals().printed.values())
check(rolled(L) == ["1:2"], "on: Greeds the material by itself, never Needs the upgrade", rolled(L))
check("/dk autoroll off" in said, "the chat line says how to turn it off", said)

L.execute("DruidKit_HelperCommand('autoroll', 'off'); ROLLED = {}; fire('START_LOOT_ROLL', 1)")
check(rolled(L) == [], "/dk autoroll off: no automatic roll", rolled(L))
L.execute("DruidKit_HelperCommand('autoroll', 'maybe')")
check(L.globals().DruidKitDB.autoRoll is False, "anything else does not turn it on", L.globals().DruidKitDB.autoRoll)
done("r5_bags_autoroll_test")
