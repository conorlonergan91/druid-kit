"""Loot roll advice: gear, party members' armour types, future gear and etiquette."""

from wowenv import runtime, source

L = runtime("ui")
L.execute("UISpecialFrames={}")
L.execute(source("DruidKit/DruidKit_Style.lua"))
L.execute(source("DruidKit/DruidKit_Bags.lua"))

L.execute(r"""
ev=frames[1]; ev.on_OnEvent(ev,"PLAYER_LOGIN")
PARTY={}
function UnitExists(u) return PARTY[u]~=nil end
function UnitClass(u) return "X", PARTY[u] end
function UnitLevel(u) if u and u~="player" then return 18 end return 12 end
ITEMS.robe[14]=1; ITEMS.mail[14]=2
ITEMS.boe={"Fancy Cloak","boe",2,15,10,"","",1,"INVTYPE_CLOAK",1,500,4,1,2}; STATS.boe={RESISTANCE0_NAME=1}
ITEMS.lth={"Leather Vest","lth",2,15,10,"","",1,"INVTYPE_CHEST",1,200,4,2,1}; STATS.lth={ITEM_MOD_STAMINA_SHORT=6,RESISTANCE0_NAME=60}
ITEMS.hi={"Future Vest","hi",2,20,15,"","",1,"INVTYPE_CHEST",1,300,4,2,1}; STATS.hi={ITEM_MOD_STAMINA_SHORT=8,RESISTANCE0_NAME=70}
function advise(item, party) PARTY=party or {}; local a,why=DruidKitBagsAPI.rollAdvice(item,true,true); return a.." | "..why end
R={
  advise("robe",{party1="MAGE"}),
  advise("lth",{party1="ROGUE"}),
  advise("boe",{party1="MAGE"}),
  advise("hi",{}),
  advise("mail",{}),
}
""")
from expect import check, done

R = list(L.globals().R.values())
for r in R:
    print(" ", r)
check(
    R[0].startswith("NEED") and "ask in /p" in R[0],
    "big cloth upgrade with a mage in the party: Need, but ask first",
    R[0],
)
check(R[1].startswith("NEED") and "rogue" in R[1], "leather upgrade: Need, and mentions the rogue", R[1])
check(
    R[2].startswith("GREED") and "Never Need just to sell" in R[2],
    "bind-on-equip non-upgrade: Greed, never Need to sell",
    R[2],
)
check(R[3].startswith("GREED") and "level 15" in R[3], "gear for later: Greed and ask", R[3])
check(R[4].startswith("GREED") and "mail" in R[4], "mail: druids can never use it", R[4])
done("roll_test")
