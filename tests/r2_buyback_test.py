"""Buyback cap: autopilot, Sell all, row Sell and Sell junk share 12 sales per vendor visit, reset when the vendor
opens again, and say how many are left."""

from expect import check, done
from wowenv import runtime, source


def run(bag):
    L = runtime("ui")
    L.execute("UISpecialFrames={}")
    L.execute(source("DruidKit/DruidKit_Style.lua"))
    L.execute(
        r"""
function GetMoney() return 0 end
SOLD = {}
C_Container.UseContainerItem = function(b, s) SOLD[#SOLD+1] = BAG[b][s]; BAG[b][s] = nil end
DruidKitDB = {}
BAG[0] = {}
for i = 1, 30 do ITEMS["g" .. i] = { "Tooth " .. i, "g" .. i, 0, 5, 0, "", "", 1, "", 1, 7, 15, 0 } end
for i = 1, 30 do ITEMS["m" .. i] = { "Chain Vest " .. i, "m" .. i, 1, 12, 8, "", "", 1, "INVTYPE_CHEST", 1, 150, 4, 3 } end
"""
        + bag
        + r"""
C_Container.GetContainerNumSlots = function(b) return b == 0 and 30 or 0 end
function said(s) local n=0 for _,p in ipairs(printed) do if p:find(s,1,true) then n=n+1 end end return n end
function click(label) for _, f in ipairs(frames) do if f.text == label and f.on_OnClick then f.on_OnClick(f); return end end end
"""
    )
    L.execute(source("DruidKit/DruidKit_Bags.lua"))
    L.execute('MerchantFrame.IsShown = function() return true end; ev = frames[1]; ev.on_OnEvent(ev, "PLAYER_LOGIN")')
    return L, L.globals()


# Autopilot sells 12; Sell all in the same visit sells nothing more and says how many are left.
L, g = run('for i = 1, 20 do BAG[0][i] = "m" .. i end')
L.execute('ev.on_OnEvent(ev, "MERCHANT_SHOW"); DruidKit_ToggleBags(); click("Sell all")')
check(len(g.SOLD) == 12, "Sell all after the autopilot's 12 sells nothing more", len(g.SOLD))
check(L.eval('said("8 more to sell")') >= 1, "it says 8 are left and to reopen the vendor")
L.execute('ev.on_OnEvent(ev, "MERCHANT_SHOW")')
check(len(g.SOLD) == 20, "reopening the vendor starts a new 12", len(g.SOLD))

# Manual Sell all (autosell off): 10 gear + 5 grey -> 12 sold, 3 left.
L, g = run('for i = 1, 10 do BAG[0][i] = "m" .. i end for i = 1, 5 do BAG[0][10 + i] = "g" .. i end')
L.execute('DruidKitDB.autoSell = false; ev.on_OnEvent(ev, "MERCHANT_SHOW"); DruidKit_ToggleBags(); click("Sell all")')
check(len(g.SOLD) == 12, "manual Sell all stops at 12", len(g.SOLD))
check(L.eval('said("3 more to sell")') >= 1, "manual Sell all says 3 are left", list(g.printed.values()))

# Sell junk button: 15 greys -> 12 sold, 3 left; a second click sells none.
L, g = run('for i = 1, 15 do BAG[0][i] = "g" .. i end')
L.execute('DruidKitDB.autoSell = false; ev.on_OnEvent(ev, "MERCHANT_SHOW"); click("Sell junk"); click("Sell junk")')
check(len(g.SOLD) == 12, "Sell junk stops at 12", len(g.SOLD))
check(L.eval('said("3 more to sell")') == 2, "Sell junk says 3 are left each time", list(g.printed.values()))

# A row Sell after the cap is reached sells nothing and says Buyback is full.
L, g = run('for i = 1, 13 do BAG[0][i] = "m" .. i end')
L.execute('ev.on_OnEvent(ev, "MERCHANT_SHOW"); DruidKit_ToggleBags(); click("Sell")')
check(len(g.SOLD) == 12, "row Sell after the cap sells nothing", len(g.SOLD))
check(L.eval('said("more to sell")') >= 2, "row Sell says how many are left", list(g.printed.values()))
done("r2_buyback_test")
