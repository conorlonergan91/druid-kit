"""Vendor autopilot re-checks each item just before selling it: one your quest has started needing since the scan
is not sold."""

from expect import check, done
from wowenv import runtime, source

L = runtime("ui")
L.execute(r"""
UISpecialFrames = {}
NOW = 100
function GetTime() return NOW end
function GetMoney() return 0 end
DruidKitDB = {}
NEED = nil
C_QuestLog = { GetNumQuestLogEntries = function() return NEED and 1 or 0 end,
  GetInfo = function() return { questID = 7, title = "Collecting" } end,
  GetQuestObjectives = function() return { { text = "0/1 " .. NEED } } end }
SOLD = {}
C_Container.UseContainerItem = function(b, s)
  local k = BAG[b][s]; SOLD[#SOLD+1] = k; BAG[b][s] = nil
  if #SOLD == 1 then NEED = (k == "grey") and "Chain Vest" or "Broken Tooth"; NOW = NOW + 10 end
end
BAG[0] = { "grey", "mail" }
C_Container.GetContainerNumSlots = function(b) return b == 0 and 2 or 0 end
""")
L.execute(source("DruidKit/DruidKit_Style.lua"))
L.execute(source("DruidKit/DruidKit_Bags.lua"))
L.execute(r"""
MerchantFrame = CreateFrame("Frame"); MerchantFrame.IsShown = function() return true end
ev = frames[1]; ev.on_OnEvent(ev, "PLAYER_LOGIN"); ev.on_OnEvent(ev, "MERCHANT_SHOW")
""")
sold = list(L.globals().SOLD.values())
check(len(sold) == 1, "the item a quest now needs is not sold", sold)
done("r4_bags_autoguard_test")
