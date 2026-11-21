"""Quest items needed much later: the update's plan (DruidKitRoute.items) banks or drops them; without a plan, an
item for a quest the route doesn't do goes to the bank list when a bank is on the way. A starter the plan
drops is only listed to check."""

from expect import check, done
from wowenv import runtime, source

L = runtime("ui")
L.execute(r"""
UISpecialFrames={}
function UnitLevel() return 20 end
function UnitClass() return "Druid", "DRUID" end
function GetTime() return 1000 end
ITEMS.powder = {"Strange Smelling Powder","powder",1,1,0,"","",1,"",1,0,12,0,4}
ITEMS.voucher = {"Free Ticket Voucher","voucher",1,1,0,"","",1,"",1,0,12,0,4}
ITEMS.lunch = {"Parker's Lunch","lunch",1,1,0,"","",1,"",1,0,12,0,4}
ITEMS.tools = {"Excavation Tools","tools",1,1,0,"","",1,"",1,0,12,0,4}
BAG = { [0] = { "powder", "voucher", "lunch", "tools" } }
C_Container.GetContainerNumSlots = function(b) return b == 0 and 4 or 0 end
local QI = { tools = { questID = 86613, isActive = false }, powder = { isQuestItem = true },
             voucher = { isQuestItem = true }, lunch = { isQuestItem = true } }
C_Container.GetContainerItemQuestInfo = function(b, s) return QI[BAG[b][s]] or {} end
LOGQ = { { questID = 161, title = "A Dark Threat Looms", obj = "Take the strange smelling powder to Ashlan." },
         { questID = 7905, title = "The Darkmoon Faire", obj = "Deliver the Free Ticket Voucher to Gelvas." },
         { questID = 129, title = "A Free Lunch", obj = "Bring Parker's lunch to Guard Parker." } }
C_QuestLog = {
  GetNumQuestLogEntries = function() return #LOGQ end,
  GetInfo = function(i) return LOGQ[i] end,
  GetQuestObjectives = function(q) for _, x in ipairs(LOGQ) do if x.questID == q then return { { text = x.obj } } end end end,
  IsQuestFlaggedCompleted = function() return false end,
}
-- The route: Darnassus (bank) soon, A Free Lunch later; nothing for 161 or 7905.
function DruidKit_StepsAhead(q) return ({ [129] = 22 })[q] end
function DruidKit_NextBank() return { steps = 5, where = "Darnassus" } end
DruidKitRoute = { id = "r", sections = {}, items = {
  ["Free Ticket Voucher"] = { action = "bank", why = "needed later for The Darkmoon Faire; bank it in Darnassus" },
  ["Excavation Tools"] = { action = "drop", why = "starts Excavation Tools; it drops again from tool piles" },
} }
""")
L.execute(source("DruidKit/DruidKit_Style.lua"))
L.execute(source("DruidKit/DruidKit_Bags.lua"))
L.execute(r"""
frames[1].on_OnEvent(frames[1], "PLAYER_LOGIN")
DruidKit_ToggleBags()
rows = {} for _, f in ipairs(allfs) do if f.text ~= "" then rows[#rows+1] = f.text end end
""")
text = "\n".join(L.globals().rows.values())
print(text)
bank = text.split("Bank these")[1].split("Sell at a vendor")[0] if "Bank these" in text else ""
drop = text.split("Sell at a vendor")[1] if "Sell at a vendor" in text else ""
check("Free Ticket Voucher" in bank and "Darkmoon" in bank, "the update's plan banks the voucher", bank)
check(
    "Strange Smelling Powder" in bank and "not in your current route" in bank,
    "no plan: banked when not in the route",
    bank,
)
check("Parker's Lunch" not in bank and "Parker's Lunch" not in drop, "an item the route still needs stays put", text)
chk = text.split("Quest items to check")[1].split("Sell at a vendor")[0] if "Quest items to check" in text else ""
check(
    "Excavation Tools" in chk and "drops again" in chk and "Excavation Tools" not in drop,
    "a starter the plan drops is shown to check, never offered to sell or destroy",
    text,
)
done("laterbank_test")
