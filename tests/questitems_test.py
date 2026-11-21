"""Quest items: ones for no quest in your log are shown to check (never offered to destroy); ones your quests
mention are kept; quest starters are announced, listed once with the count, and offered to destroy when the quest
is done. Auctionator prices move valuable items to an Auction House list."""

from expect import check, done
from wowenv import runtime, source

L = runtime("ui")
L.execute(r"""
UISpecialFrames={}
function UnitLevel() return 20 end
function UnitClass() return "Druid", "DRUID" end
function GetTime() return 1000 end
RaidWarningFrame = {}; function RaidNotice_AddMessage(_, m) WARN = m end
--         name, link, q, ilvl, minLvl, type, sub, stack, equipLoc, icon, price, classID, subID, bindType
ITEMS.powder = {"Strange Smelling Powder","powder",1,1,0,"","",1,"",1,0,12,0,4}
ITEMS.oldkey = {"Gnoll Paw","oldkey",1,1,0,"","",1,"",1,0,12,0,4}
ITEMS.tools = {"Excavation Tools","tools",1,1,0,"","",1,"",1,0,12,0,4}
ITEMS.oldstart = {"Torn Map","oldstart",1,1,0,"","",1,"",1,0,12,0,4}
ITEMS.silk = {"Silk Cloth","silk",1,15,0,"","",20,"",1,40,7,5,0}
BAG = { [0] = { "powder", "oldkey", "tools", "tools", "tools", "oldstart", "silk" } }
C_Container.GetContainerNumSlots = function(b) return b == 0 and 7 or 0 end
local QI = { tools = { isQuestItem = false, questID = 86613, isActive = false },
             oldstart = { isQuestItem = false, questID = 500, isActive = false },
             powder = { isQuestItem = true }, oldkey = { isQuestItem = true } }
C_Container.GetContainerItemQuestInfo = function(b, s) return QI[BAG[b][s]] or {} end
C_QuestLog = {
  GetNumQuestLogEntries = function() return 1 end,
  GetInfo = function() return { questID = 161, title = "A Dark Threat Looms" } end,
  GetQuestObjectives = function() return { { text = "Take the strange smelling powder to Ashlan Stonesmirk." } } end,
  IsQuestFlaggedCompleted = function(q) return q == 500 end,
}
Auctionator = { API = { v1 = { GetAuctionPriceByItemLink = function(_, l) return ({ silk = 300 })[KEY(l)] end } } }
function DruidKit_NeededFor(n) return false, true, false end
""")
L.execute(source("DruidKit/DruidKit_Style.lua"))
L.execute(source("DruidKit/DruidKit_Bags.lua"))
L.execute(r"""
frames[1].on_OnEvent(frames[1], "PLAYER_LOGIN")
for _, f in ipairs(frames) do if f.on_OnEvent then f.on_OnEvent(f, "BAG_UPDATE_DELAYED") end end
DruidKit_ToggleBags()
rows = {} for _, f in ipairs(allfs) do if f.text ~= "" then rows[#rows+1] = f.text end end
ST = DruidKit_QuestStarters()
R = { WARN or "", #ST, ST[1] and ST[1].name or "" }
""")
g = L.globals()
rows = list(g.rows.values())
text = "\n".join(rows)
print(text)
r = list(g.R.values())
print(r)
use = text.split("Use these")[1].split("\n")[0:8] if "Use these" in text else []
use = "\n".join(use)
check("Excavation Tools" in use and "you have 3" in use, "a quest starter is listed once with the count", use)
check("Torn Map" in text and "already done" in text, "a starter for a finished quest is offered to destroy", text)
check(
    "Gnoll Paw" in text and "may belong to no quest" in text,
    "a quest item for no quest you have is shown to check",
    text,
)
sell = text.split("Sell at a vendor")[1] if "Sell at a vendor" in text else text
check("Strange Smelling Powder" not in sell, "a quest item your quest mentions is kept", sell)
check("Excavation Tools" in r[0] and "right-click" in r[0], "a new quest starter is announced on screen", r[0])
check(r[1] == 1 and r[2] == "Excavation Tools", "the step window gets the waiting starter", r[1:])
ah = text.split("Auction House\n(")[1].split("Sell at a vendor")[0] if "Auction House\n(" in text else ""
check("Silk Cloth" in ah and "a vendor pays" in ah, "Auctionator price well above vendor -> Auction House list", text)
done("questitems_test")
