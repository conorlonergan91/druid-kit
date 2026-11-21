"""Bank check: what it tells you to store (library books, quest items needed much later) is never then offered
back as 'take out'."""

from expect import check, done
from wowenv import runtime, source

L = runtime("ui")
L.execute(r"""
UISpecialFrames = {}
function GetTime() return 100 end
ITEMS.book = {"Venomous Journeys","book",1,1,0,"","",1,"",1,0,12,0,4}
ITEMS.crate = {"Gnome Gear","crate",1,1,0,"","",1,"",1,0,12,0,4}
BAG[0] = { "book", "crate" }
BAG[-1] = { "book", "crate" }
C_Container.GetContainerNumSlots = function(b) if b == 0 then return 3 elseif b == -1 then return 2 end return 0 end
C_Container.GetContainerItemQuestInfo = function(b, s) return { isQuestItem = true } end
C_QuestLog = { GetNumQuestLogEntries = function() return 1 end,
  GetInfo = function() return { questID = 7, title = "Gnome Gear" } end,
  GetQuestObjectives = function() return { { text = "0/1 Gnome Gear" } } end }
DruidKitRoute = { items = { ["Gnome Gear"] = { action = "bank", why = "needed at level 30: bank it" } } }
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
print(text)
take = text.split("Take out")[1].split("Put in the bank")[0]
store = text.split("Put in the bank")[1]
check("Venomous Journeys" in store and "Gnome Gear" in store, "book and later quest item: store them", store)
check("Venomous Journeys" not in take, "a library book in the bank is not offered back", take)
check("Gnome Gear" not in take, "a quest item banked for later is not offered back", take)
done("bagsfix_bank_test")
