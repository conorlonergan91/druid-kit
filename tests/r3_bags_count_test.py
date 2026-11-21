"""Destroy and Sell act only on the stack you were shown: a slot that now holds a different count of the same item
(stacks merged or split since) is left alone."""

from expect import check, done
from wowenv import runtime, source

L = runtime("ui")
L.execute(r"""
UISpecialFrames = {}
DruidKitDB = { autoSell = false }
BAG[0] = {"mail"}
C_Container.GetContainerNumSlots = function(b) return b == 0 and 1 or 0 end
C_Container.UseContainerItem = function(b, s) SOLD = b .. ":" .. s end
C_Container.PickupContainerItem = function(b, s) picked = b .. ":" .. s end
function DeleteCursorItem() deleted = picked end
function ClearCursor() end
function StaticPopup_Show() DLG = {}; return DLG end
""")
L.execute(source("DruidKit/DruidKit_Style.lua"))
L.execute(source("DruidKit/DruidKit_Bags.lua"))
L.execute(r"""
DruidKit_ConfirmDestroy({ bag = 0, slot = 1, link = LINK("mail"), count = 1 })
ITEMS.mail[8] = 2
StaticPopupDialogs.DRUIDKIT_DESTROY.OnAccept(nil, DLG.data)
ITEMS.mail[8] = 1
MerchantFrame.IsShown = function() return true end
DruidKit_ToggleBags()
ITEMS.mail[8] = 2
for _, f in ipairs(frames) do if f.text == "Sell" and f.on_OnClick then f.on_OnClick(); break end end
""")
g = L.globals()
check(g.deleted is None, "destroy refuses when the stack count changed", g.deleted)
check(g.SOLD is None, "sell refuses when the stack count changed", g.SOLD)
done("r3_bags_count_test")
