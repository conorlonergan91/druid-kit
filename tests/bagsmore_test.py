"""More bag check cases: mage scrolls (Comprehension) are sold not used, bag items are compared with the bags you
use, and Bind on Equip greens you can't use point at the Auction House."""

from expect import check, done
from wowenv import runtime, source

L = runtime("ui")
L.execute(r"""
UISpecialFrames={}
function UnitLevel() return 20 end
function UnitClass() return "Druid", "DRUID" end
ITEM_BIND_ON_EQUIP = "Binds when equipped"
TIPS = {
  scroll = { "Scroll of Frog Familiar", "Requires Comprehension (25)", "Use: Teaches you Frog Familiar." },
  scroll0 = { "Scroll of Cryoblast", "Requires Comprehension (40)" },
  bag8 = { "Small Silk Pack", "8 Slot Bag" },
  bag6 = { "Red Linen Bag", "6 Slot Bag" },
  mailboe = { "Chain Gloves of the Bear", "Binds when equipped", "Mail" },
}
C_TooltipInfo = { GetHyperlink = function(l) local t = TIPS[l] or { l }; local lines = {}
  for i, x in ipairs(t) do lines[i] = { leftText = x } end; return { lines = lines } end }
function GetNumSkillLines() return 1 end
function GetSkillLineInfo() return "Alchemy", false, nil, 89 end
ITEMS.scroll = {"Scroll of Frog Familiar","scroll",2,20,10,"","",1,"",1,300,9,0}
ITEMS.scroll0 = {"Scroll of Cryoblast","scroll0",2,25,15,"","",1,"",1,400,0,8}
ITEMS.bag8 = {"Small Silk Pack","bag8",1,20,0,"","",1,"INVTYPE_BAG",1,500,1,0}
ITEMS.bag6 = {"Red Linen Bag","bag6",1,10,0,"","",1,"INVTYPE_BAG",1,100,1,0}
ITEMS.mailboe = {"Chain Gloves of the Bear","mailboe",2,20,15,"","",1,"INVTYPE_HAND",1,700,4,3}
BAG = { [0] = { "scroll", "scroll0", "bag8", "bag6", "mailboe" } }
SLOTSN = { [0] = 5, [1] = 10, [2] = 10, [3] = 10, [4] = 6 }
C_Container.GetContainerNumSlots = function(b) return SLOTSN[b] or 0 end
""")
L.execute(source("DruidKit/DruidKit_Style.lua"))
L.execute(source("DruidKit/DruidKit_Bags.lua"))
L.execute(r"""
frames[1].on_OnEvent(frames[1], "PLAYER_LOGIN")
DruidKit_ToggleBags()
rows = {} for _, f in ipairs(allfs) do if f.text ~= "" then rows[#rows+1] = f.text end end
""")
rows = list(L.globals().rows.values())
text = "\n".join(rows)
print(text)
use = text.split("Use these")[1].split("Sell at a vendor")[0] if "Use these" in text else ""
sell = text.split("Sell at a vendor")[1] if "Sell at a vendor" in text else ""
check("Frog Familiar" not in use and "Cryoblast" not in use, "mage scrolls are never in 'Use these'", use)
check(sell.count("Mage scroll") >= 2 and "Auction House" in sell, "mage scrolls go to the sell list (or AH)", sell)
check("Small Silk Pack" in use and "more than your 6-slot bag" in use, "a bigger bag is offered as a swap", use)
check("Red Linen Bag" in sell and "6-slot bag: no bigger" in sell, "a bag no bigger than yours is sold", sell)
check("binds when equipped" in sell.lower(), "unusable BoE greens point at the Auction House", sell)
done("bagsmore_test")
