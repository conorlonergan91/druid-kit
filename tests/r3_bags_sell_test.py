"""Vendor autopilot never sells what it can't judge or can use later: idols and on-use trinkets (no stats to
score), an off-hand while you wield a two-hander, and items needing a higher profession rank (banked). Quest
starters for a done quest are listed to check, never offered to sell or destroy."""

from expect import check, done
from wowenv import runtime, source


def run(extra):
    L = runtime("ui")
    L.execute("UISpecialFrames={}")
    L.execute(source("DruidKit/DruidKit_Style.lua"))
    L.execute(
        r"""
function GetMoney() return 0 end
SOLD = {}
C_Container.UseContainerItem = function(b, s) SOLD[#SOLD+1] = BAG[b][s]; BAG[b][s] = nil end
DruidKitDB = {}
TIP = {}
C_TooltipInfo = { GetHyperlink = function(l) local t = TIP[KEY(l)]; return { lines = t and { { leftText = t } } or {} } end }
LINES = { { "Professions", true, true }, { "Engineering", false, false, 100 },
          { "Secondary Skills", true, true }, { "First Aid", false, false, 40 } }
function GetNumSkillLines() return #LINES end
function GetSkillLineInfo(i) local l = LINES[i]; if l then return l[1], l[2], l[3], l[4] end end
"""
        + extra
        + "\nC_Container.GetContainerNumSlots = function(b) return b == 0 and #BAG[0] or 0 end"
    )
    L.execute(source("DruidKit/DruidKit_Bags.lua"))
    L.execute(r"""
MerchantFrame.IsShown = function() return true end
ev = frames[1]; ev.on_OnEvent(ev, 'PLAYER_LOGIN'); ev.on_OnEvent(ev, 'MERCHANT_SHOW')
MerchantFrame.IsShown = function() return false end
DruidKit_ToggleBags()
rows = {} for _, f in ipairs(allfs) do if f.text ~= "" then rows[#rows+1] = f.text end end
""")
    g = L.globals()
    return [g.SOLD[k] for k in g.SOLD], "\n".join(g.rows.values())


def section(text, head):
    return text.split(head)[1].split("Sell at a vendor")[0] if head in text else ""


sold, text = run(r"""
ITEMS.idol = {"Idol of Something","idol",3,30,10,"","",1,"INVTYPE_RELIC",1,500,4,8,1}
ITEMS.trink = {"Shiny Trinket","trink",2,30,10,"","",1,"INVTYPE_TRINKET",1,400,4,0,1}
BAG[0] = {"idol", "trink"}
""")
check(sold == [], "BoP idol and on-use trinket (no stats) are not sold", sold)
kept = section(text, "Gear you're keeping")
check("Idol of Something" in kept and "Shiny Trinket" in kept, "they're listed as kept, not to sell", text)

sold, text = run(r"""
ITEMS.staff = {"Old Staff","staff",1,10,5,"","",1,"INVTYPE_2HWEAPON",1,100,2,10,1}
ITEMS.oh = {"Great Orb","oh",1,15,10,"","",1,"INVTYPE_HOLDABLE",1,300,4,0,1}
STATS.staff = {ITEM_MOD_STAMINA_SHORT=2}
STATS.oh = {ITEM_MOD_STAMINA_SHORT=8, ITEM_MOD_INTELLECT_SHORT=8}
EQ[16] = "staff"
BAG[0] = {"oh"}
""")
check(sold == [], "an off-hand while wielding a two-hander is not sold", sold)
check("Great Orb" in section(text, "Gear you're keeping"), "the off-hand is kept", text)

sold, text = run(r"""
ITEMS.band = {"Silk Bandage","band",1,20,0,"","",20,"",1,28,0,7}
ITEMS.wool = {"Wool Bandage","wool",1,10,0,"","",20,"",1,10,0,7}
ITEMS.gog = {"Flying Goggles","gog",1,20,10,"","",1,"INVTYPE_HEAD",1,300,4,1}
STATS.gog = {ITEM_MOD_STAMINA_SHORT=1}
TIP.band = "Requires First Aid (50)"; TIP.gog = "Requires Engineering (150)"
BAG[0] = {"band", "wool", "gog"}
""")
check(sold == [], "items needing a higher First Aid / Engineering rank are not sold", sold)
bank = section(text, "Bank these")
check("Silk Bandage" in bank and "Flying Goggles" in bank, "they're banked till you reach the rank", text)

sold, text = run(r"""
ITEMS.start = {"Old Letter","start",1,5,0,"","",1,"",1,25,15,0}
BAG[0] = {"start"}
C_Container.GetContainerItemQuestInfo = function() return { isQuestItem = false, questID = 99, isActive = false } end
C_QuestLog = { IsQuestFlaggedCompleted = function() return true end }
""")
chk = section(text, "Quest items to check")
drop = text.split("Bags full?")[1] if "Bags full?" in text else ""
check(sold == [], "a starter for a done quest is not sold", sold)
check("Old Letter" in chk and "Old Letter" not in drop, "it's listed to check, not offered to destroy", text)
done("r3_bags_sell_test")
