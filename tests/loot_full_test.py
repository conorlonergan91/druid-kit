"""Bags full while looting: gear worth taking is shouted on screen (with a sound), and if you close the loot and
leave it on the corpse, you're told so."""

from expect import check, done
from wowenv import runtime, source

L = runtime("ui")
L.execute(r"""
UISpecialFrames={}
function UnitLevel() return 20 end
function GetTime() return 100 end
SOUNDKIT = { RAID_WARNING = 8959 }; function PlaySound(id) SOUNDS = (SOUNDS or 0) + 1 end
RaidWarningFrame = {}; function RaidNotice_AddMessage(_, msg) WARN = msg end
ITEMS["greatrobe"] = {"Robe of the Moon","greatrobe",2,20,15,"","",1,"INVTYPE_ROBE",1,900,4,1}
STATS.greatrobe = {ITEM_MOD_STAMINA_SHORT=9,ITEM_MOD_INTELLECT_SHORT=8,RESISTANCE0_NAME=40}
LOOT = { { name = "Robe of the Moon", link = "greatrobe" }, { name = "Broken Tooth", link = "grey" } }
function GetNumLootItems() return #LOOT end
function GetLootSlotType() return 1 end
function GetLootSlotInfo(i) local l = LOOT[i]; if l then return 1, l.name, 1, nil, 2, nil, false end end
function GetLootSlotLink(i) return LOOT[i] and LOOT[i].link end
""")
L.execute(source("DruidKit/DruidKit_Style.lua"))
L.execute(source("DruidKit/DruidKit_Bags.lua"))
L.execute(r"""
frames[1].on_OnEvent(frames[1], "PLAYER_LOGIN")
function fire(e, a) for _, f in ipairs(frames) do if f.on_OnEvent then pcall(f.on_OnEvent, f, e, a) end end end
R = {}
fire("LOOT_OPENED")
R[1] = WARN or ""; R[2] = SOUNDS or 0
WARN = nil
fire("LOOT_CLOSED")
R[3] = WARN or ""
-- second corpse: you take it after making room
WARN = nil; GetTime = function() return 500 end
fire("LOOT_OPENED")
table.remove(LOOT, 1); fire("LOOT_SLOT_CLEARED", 1)
WARN = nil
fire("LOOT_CLOSED")
R[4] = WARN or ""
""")
r = list(L.globals().R.values())
print(r)
check(
    "worth taking: Robe of the Moon" in r[0] and "upgrade" in r[0],
    "bags full: the upgrade in the loot is shouted",
    r[0],
)
check(r[1] >= 1, "with a sound as a second signal", r[1])
check("LEFT ON THE CORPSE: Robe of the Moon" in r[2], "closing the loot without it says it's left behind", r[2])
check(r[3] == "", "no warning once you've taken it", r[3])
check("worth taking: Broken Tooth" not in r[0] and "CORPSE: Broken Tooth" not in r[2], "grey junk is never shouted", r)
done("loot_full_test")
