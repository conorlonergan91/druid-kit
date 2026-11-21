"""Vendor autopilot: never more than the Buyback tab holds (12) per visit, never potions or elixirs (the panel
footer promises that), and Sell junk's sales are logged like the autopilot's."""

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
"""
        + extra
    )
    L.execute(source("DruidKit/DruidKit_Bags.lua"))
    L.execute("MerchantFrame.IsShown = function() return true end")
    return L


# 20 different unusable mail pieces: only 12 are sold in one visit.
L = run(r"""
BAG[0] = {}
for i = 1, 20 do
  local k = "mail" .. i
  ITEMS[k] = { "Chain Vest " .. i, k, 1, 12, 8, "", "", 1, "INVTYPE_CHEST", 1, 150, 4, 3 }
  BAG[0][i] = k
end
C_Container.GetContainerNumSlots = function(b) return b == 0 and 20 or 0 end
""")
L.execute('ev = frames[1]; ev.on_OnEvent(ev, "PLAYER_LOGIN"); ev.on_OnEvent(ev, "MERCHANT_SHOW")')
sold = list(L.globals().SOLD.values())
check(len(sold) == 12, "autopilot sells at most 12 per visit (what Buyback holds)", len(sold))

# Extra potions and elixirs stay; the Sell list doesn't offer them either.
L = run(r"""
ITEMS.elix1 = {"Elixir of Minor Strength","elix1",1,5,2,"","",20,"",1,10,0,2}
ITEMS.elix2 = {"Elixir of Minor Strength","elix2",1,5,2,"","",20,"",1,10,0,2}
ITEMS.pot1 = {"Minor Healing Potion","pot1",1,5,1,"","",20,"",1,5,0,1}
ITEMS.pot2 = {"Minor Healing Potion","pot2",1,5,1,"","",20,"",1,5,0,1}
COUNTS = { elix1 = 8, elix2 = 2, pot1 = 20, pot2 = 5 }
local gi = C_Container.GetContainerItemInfo
C_Container.GetContainerItemInfo = function(b, s) local r = gi(b, s); if r and COUNTS[KEY(r.hyperlink)] then r.stackCount = COUNTS[KEY(r.hyperlink)] end return r end
BAG[0] = { "elix1", "elix2", "pot1", "pot2", "grey" }
C_Container.GetContainerNumSlots = function(b) return b == 0 and 5 or 0 end
""")
L.execute(r"""
ev = frames[1]; ev.on_OnEvent(ev, "PLAYER_LOGIN")
MerchantFrame.IsShown = function() return false end
DruidKit_ToggleBags()
rows = {} for _, f in ipairs(allfs) do if f.text ~= "" then rows[#rows + 1] = f.text end end
MerchantFrame.IsShown = function() return true end
ev.on_OnEvent(ev, "MERCHANT_SHOW")
""")
g = L.globals()
sold = list(g.SOLD.values())
text = "\n".join(g.rows.values())
check(sold == ["grey"], "autopilot sells no potions or elixirs", sold)
sell = text.split("Sell at a vendor")[1].split("Bags full?")[0]
check("Elixir" not in sell and "Potion" not in sell, "the Sell list doesn't offer them", sell)
check("potions" in text, "footer still promises no potions", text)

# Sell junk logs what it sold.
L = run("")
L.execute(
    'ev = frames[1]; ev.on_OnEvent(ev, "PLAYER_LOGIN"); DruidKitDB.autoSell = false; ev.on_OnEvent(ev, "MERCHANT_SHOW")'
)
L.execute('for _, f in ipairs(frames) do if f.text == "Sell junk" and f.on_OnClick then f.on_OnClick() end end')
g = L.globals()
log = g.DruidKitDB.soldLog
names = [e.name for e in log.values()] if log else []
check(list(g.SOLD.values()) == ["grey"] and names == ["Broken Tooth"], "Sell junk's sales go to the sold log", names)
done("bagsfix_vendor_test")
