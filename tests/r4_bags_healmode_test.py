"""Healing mode: a plain weapon that scores nothing for healing is still compared (and sold when worse); only an
item with no stats for either role is kept as "can't compare"."""

from expect import check, done
from wowenv import runtime, source

L = runtime("ui")
L.execute("UISpecialFrames={}")
L.execute(source("DruidKit/DruidKit_Style.lua"))
L.execute(r"""
function GetMoney() return 0 end
SOLD = {}
C_Container.UseContainerItem = function(b, s) SOLD[#SOLD+1] = BAG[b][s]; BAG[b][s] = nil end
DruidKitDB = { barMode = "heal" }
ITEMS.club = {"Spiked Club","club",1,10,5,"","",1,"INVTYPE_WEAPON",1,200,2,4,1}
ITEMS.big = {"Heavy Mace","big",1,15,10,"","",1,"INVTYPE_WEAPON",1,400,2,4,1}
ITEMS.idol = {"Idol of Something","idol",3,30,10,"","",1,"INVTYPE_RELIC",1,500,4,8,1}
STATS.club = {ITEM_MOD_STRENGTH_SHORT=2, ITEM_MOD_DAMAGE_PER_SECOND_SHORT=3}
STATS.big = {ITEM_MOD_STRENGTH_SHORT=5, ITEM_MOD_DAMAGE_PER_SECOND_SHORT=6}
EQ[16] = "big"
BAG[0] = {"club", "idol"}
C_Container.GetContainerNumSlots = function(b) return b == 0 and #BAG[0] or 0 end
""")
L.execute(source("DruidKit/DruidKit_Bags.lua"))
L.execute(r"""
MerchantFrame.IsShown = function() return true end
ev = frames[1]; ev.on_OnEvent(ev, 'PLAYER_LOGIN'); ev.on_OnEvent(ev, 'MERCHANT_SHOW')
""")
sold = list(L.globals().SOLD.values())
check("club" in sold, "healing mode: a worse plain weapon is sold", sold)
check("idol" not in sold, "an idol with no stats for either role is kept", sold)
done("r4_bags_healmode_test")
