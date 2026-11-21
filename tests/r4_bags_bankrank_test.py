"""Bank check agrees with Bag check: an item needing a higher profession rank goes in the bank and isn't offered
back out."""

from expect import check, done
from wowenv import runtime, source

L = runtime("ui")
L.execute(r"""
UISpecialFrames = {}
function GetTime() return 100 end
DruidKitDB = {}
ITEMS.band = {"Silk Bandage","band",1,20,0,"","",20,"",1,28,0,7}
BAG[0] = { "band" }
BAG[-1] = { "band" }
C_Container.GetContainerNumSlots = function(b) if b == 0 then return 2 elseif b == -1 then return 1 end return 0 end
C_Container.GetContainerItemQuestInfo = function() return {} end
C_TooltipInfo = { GetHyperlink = function(l)
  return { lines = { { leftText = "Requires First Aid (50)", leftColor = { r = 1, g = 0.1, b = 0.1 } } } } end }
LINES = { { "Secondary Skills", true, true }, { "First Aid", false, false, 40 } }
function GetNumSkillLines() return #LINES end
function GetSkillLineInfo(i) local l = LINES[i]; if l then return l[1], l[2], l[3], l[4] end end
BankFrame = { IsShown = function() return false end }
""")
L.execute(source("DruidKit/DruidKit_Style.lua"))
L.execute(source("DruidKit/DruidKit_Bags.lua"))
L.execute(source("DruidKit/DruidKit_Bank.lua"))
L.execute(r"""
for _, f in ipairs(frames) do if f.on_OnEvent then f.on_OnEvent(f, "PLAYER_LOGIN") end end
allfs = {}
for _, f in ipairs(frames) do if f.on_OnEvent then f.on_OnEvent(f, "BANKFRAME_OPENED") end end
texts = {} for _, f in ipairs(allfs) do if f.text ~= "" then texts[#texts + 1] = f.text end end
""")
text = "\n".join(L.globals().texts.values())
take = text.split("Take out")[1].split("Put in the bank")[0]
store = text.split("Put in the bank")[1]
check("Silk Bandage" in store and "First Aid 50" in store, "rank-locked bandage: store it", text)
check("Silk Bandage" not in take, "a rank-locked bandage in the bank is not offered back", take)
done("r4_bags_bankrank_test")
