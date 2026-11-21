"""Destroy and Sell from the drop list re-check the bag slot when clicked, not when the panel was drawn."""

from expect import check, done
from wowenv import runtime, source


def setup():
    L = runtime("ui")
    L.execute(r"""
UISpecialFrames = {}
NOW = 100; function GetTime() return NOW end
C_Container.PickupContainerItem = function(b, s) picked = b .. ":" .. s end
function DeleteCursorItem() deleted = picked end
function ClearCursor() end
function StaticPopup_Show(n, a, b) POP = { a, b }; DLG = {}; return DLG end
SOLD = {}
C_Container.UseContainerItem = function(b, s) SOLD[#SOLD + 1] = BAG[b][s] end
QUEST = {}
C_QuestLog = { GetNumQuestLogEntries = function() return #QUEST end,
  GetInfo = function(i) return { questID = 1, title = "Teeth" } end,
  GetQuestObjectives = function() return QUEST end }
""")
    L.execute(source("DruidKit/DruidKit_Style.lua"))
    L.execute(source("DruidKit/DruidKit_Bags.lua"))
    L.execute(r"""
function rows() local out = {} for _, f in ipairs(frames) do if f.btn and f.name and f.detail then out[#out + 1] = f end end return out end
function button(label, name, detail)
  for _, r in ipairs(rows()) do
    if r.btn.text == label and r.btn.shown and r.name.text:find(name, 1, true) and (not detail or r.detail.text:find(detail, 1, true)) then
      return r.btn.on_OnClick
    end
  end
end
""")
    return L


# 1. Destroy: the slot now holds something else -> nothing is deleted.
L = setup()
L.execute(r"""
DruidKit_ToggleBags()
button("Destroy", "Broken Tooth")()
BAG[0][3] = "robe"
StaticPopupDialogs.DRUIDKIT_DESTROY.OnAccept(nil, DLG.data)
""")
g = L.globals()
said = list(g.printed.values())
check(g.deleted is None, "destroy refuses when the slot holds a different item now", g.deleted)
check(any("Destroy" not in p and ("changed" in p or "moved" in p) for p in said), "and says why", said[-2:])

# 1b. Destroy: same item, but a quest now needs it -> nothing is deleted.
L = setup()
L.execute(r"""
DruidKit_ToggleBags()
button("Destroy", "Broken Tooth")()
QUEST[1] = { text = "0/5 Broken Tooth" }; NOW = 200
StaticPopupDialogs.DRUIDKIT_DESTROY.OnAccept(nil, DLG.data)
""")
g = L.globals()
check(g.deleted is None, "destroy refuses an item your quest needs now", g.deleted)
check(any("quest needs" in p for p in g.printed.values()), "and says why", list(g.printed.values())[-1:])

# 1c. Destroy still works when nothing changed.
L = setup()
L.execute(r"""
DruidKit_ToggleBags()
button("Destroy", "Broken Tooth")()
StaticPopupDialogs.DRUIDKIT_DESTROY.OnAccept(nil, DLG.data)
""")
check(L.globals().deleted == "0:3", "unchanged slot: destroy deletes it", L.globals().deleted)

# 2. Drop list Sell: vendor closed since the panel was drawn, or the slot changed -> nothing sold.
L = setup()
L.execute(r"""
MerchantFrame.shown = true
DruidKit_ToggleBags()
sellVest = button("Sell", "Chain Vest", "sells for")
MerchantFrame.shown = false
sellVest()
n1 = #SOLD
MerchantFrame.shown = true
BAG[0][2] = "boots"
sellVest()
n2 = #SOLD
BAG[0][2] = "mail"
sellVest()
""")
g = L.globals()
check(g.n1 == 0, "drop-list Sell does nothing once the vendor is closed", g.n1)
check(g.n2 == 0, "drop-list Sell does nothing when the slot holds something else", g.n2)
check(list(g.SOLD.values()) == ["mail"], "drop-list Sell sells the listed item", list(g.SOLD.values()))
done("bagsfix_destroy_test")
