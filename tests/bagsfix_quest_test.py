"""A quest item that looks like it belongs to no quest is only a guess: it is never offered to sell, drop or destroy
(nor as the loot helper's 'destroy this to make room'), only shown as a note to check."""

from expect import check, done
from wowenv import runtime, source

L = runtime("ui")
L.execute(r"""
UISpecialFrames = {}
function GetTime() return 100 end
function UnitLevel() return 20 end
RaidWarningFrame = {}; function RaidNotice_AddMessage(_, m) WARN = m end
--             name, link, q, ilvl, minLvl, type, sub, stack, equipLoc, icon, price, classID, subID, bindType
ITEMS.paw = { "Gnoll Paw", "paw", 1, 1, 0, "", "", 1, "", 1, 1, 12, 0, 4 }
ITEMS.sigil = { "Old Sigil", "sigil", 1, 1, 0, "", "", 1, "", 1, 50, 15, 0, 4 }
BAG[0] = { "paw", "sigil", "robe", "herb" }
C_Container.GetContainerNumSlots = function(b) return b == 0 and 4 or 0 end
C_Container.GetContainerItemQuestInfo = function() return {} end
SOLD = {}
C_Container.UseContainerItem = function(b, s) SOLD[#SOLD + 1] = BAG[b][s] end
MONEY = 0; function GetMoney() return MONEY end
DruidKitDB = {}
LOOT = { { name = "Linen Cloth", link = "herb" } }
function GetNumLootItems() return #LOOT end
function GetLootSlotType() return 1 end
function GetLootSlotInfo(i) local l = LOOT[i]; if l then return 1, l.name, 1, nil, 1, nil, false end end
function GetLootSlotLink(i) return LOOT[i] and LINK(LOOT[i].link) end
""")
L.execute(source("DruidKit/DruidKit_Style.lua"))
L.execute(source("DruidKit/DruidKit_Bags.lua"))
L.execute(r"""
frames[1].on_OnEvent(frames[1], "PLAYER_LOGIN")
DruidKit_ToggleBags()
rows = {} for _, f in ipairs(allfs) do if f.text ~= "" then rows[#rows + 1] = f.text end end
C_Container.GetContainerNumSlots = function(b) return b == 0 and 4 or 0 end
for _, f in ipairs(frames) do if f.on_OnEvent then pcall(f.on_OnEvent, f, "LOOT_OPENED") end end
DROPBTN = nil
for _, f in ipairs(frames) do if type(f.text) == "string" and f.text:find("^Destroy ") then DROPBTN = f.text end end
MerchantFrame.IsShown = function() return true end
frames[1].on_OnEvent(frames[1], "MERCHANT_SHOW")
""")
g = L.globals()
text = "\n".join(g.rows.values())
print(text)
sell = text.split("Sell at a vendor")[1] if "Sell at a vendor" in text else ""
for item in ("Gnoll Paw", "Old Sigil"):
    check(item not in sell, f"{item} (quest item, guessed orphan) is not on the sell or drop lists", sell)
    check(item in text.split("Sell at a vendor")[0], f"{item} is still shown, to check", text)
check("may belong to no quest" in text, "the note says it's a guess", text)
check(
    "Gnoll Paw" not in str(g.DROPBTN) and "Old Sigil" not in str(g.DROPBTN),
    "loot helper never says destroy it",
    g.DROPBTN,
)
sold = list(g.SOLD.values())
check("paw" not in sold and "sigil" not in sold, "the autopilot never sells it", sold)
done("bagsfix_quest_test")
