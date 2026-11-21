"""Bag check never recommends what a druid can't use: class-only gear ("Classes: Rogue") and recipes or items for
a profession you don't have."""

from expect import check, done
from wowenv import runtime, source

L = runtime("ui")
L.execute(r"""
UISpecialFrames={}
function UnitLevel() return 20 end
function UnitClass() return "Druid", "DRUID" end
ITEM_CLASSES_ALLOWED = "Classes: %s"
TIPS = {
  roguechest = { "Shadowcraft Tunic", "Classes: Rogue" },
  druidchest = { "Wildheart Vest", "Classes: Druid" },
  tailorpat = { "Pattern: Red Linen Robe", "Requires Tailoring (40)" },
  alchrec = { "Recipe: Elixir of Wisdom", "Requires Alchemy (80)" },
  engitem = { "Mechanical Squirrel", "Requires Engineering (75)" },
  magebook = { "Tome of Frost Nova", "Classes: Mage" },
}
C_TooltipInfo = { GetHyperlink = function(l) l = KEY(l); local t = TIPS[l] or { l }; local lines = {}
  for i, x in ipairs(t) do lines[i] = { leftText = x } end; return { lines = lines } end }
function GetNumSkillLines() return 1 end
function GetSkillLineInfo(i) return "Alchemy", false, nil, 89 end
ITEMS.roguechest = {"Shadowcraft Tunic","roguechest",3,30,18,"","",1,"INVTYPE_CHEST",1,900,4,2}
STATS.roguechest = {ITEM_MOD_AGILITY_SHORT=12,ITEM_MOD_STAMINA_SHORT=10,RESISTANCE0_NAME=90}
ITEMS.druidchest = {"Wildheart Vest","druidchest",3,30,18,"","",1,"INVTYPE_CHEST",1,900,4,2}
STATS.druidchest = {ITEM_MOD_AGILITY_SHORT=10,ITEM_MOD_STAMINA_SHORT=8,RESISTANCE0_NAME=80}
ITEMS.magebook = {"Tome of Frost Nova","magebook",2,20,16,"","",1,"",1,250,9,0}
ITEMS.tailorpat = {"Pattern: Red Linen Robe","tailorpat",1,10,0,"","",1,"",1,50,9,2}
ITEMS.alchrec = {"Recipe: Elixir of Wisdom","alchrec",1,10,0,"","",1,"",1,50,9,6}
BAG = { [0] = { "roguechest", "druidchest", "tailorpat", "alchrec", "grey", "herb", "oldchest", "magebook" } }
C_Container.GetContainerNumSlots = function(b) return b == 0 and 8 or 0 end
""")
L.execute(source("DruidKit/DruidKit_Style.lua"))
L.execute(source("DruidKit/DruidKit_Bags.lua"))
L.execute(r"""
frames[1].on_OnEvent(frames[1], "PLAYER_LOGIN")
DruidKit_ToggleBags()
rows = {} for _, f in ipairs(allfs) do if f.text ~= "" then rows[#rows+1] = f.text end end
R = { DruidKit_ItemRestriction("roguechest") or "", DruidKit_ItemRestriction("druidchest") or "",
      DruidKit_ItemRestriction("tailorpat") or "", DruidKit_ItemRestriction("alchrec") or "",
      DruidKit_ItemRestriction("engitem") or "" }
""")
g = L.globals()
rows = list(g.rows.values())
r = list(g.R.values())
print(r)
for x in rows:
    print("ROW", x)
check(r[0] == "for Rogue only" and r[1] == "", "class-only gear is spotted from the tooltip", r[:2])
check("Tailoring" in r[2] and r[3] == "", "profession you don't have vs one you do", r[2:4])
check("Engineering" in r[4], "any item needing a missing profession", r[4])
text = "\n".join(rows)
use_part = text.split("Use these")[1].split("Sell at a vendor")[0] if "Use these" in text else ""
check("Pattern: Red Linen Robe" not in use_part, "a Tailoring pattern is not offered to learn", use_part)
check("Tome of Frost Nova" not in use_part and "For Mage only" in text, "a mage book is never 'learn it'", use_part)
check("Recipe: Elixir of Wisdom" in use_part, "an Alchemy recipe you can learn is offered", use_part)
check(any("for rogue only" in x.lower() for x in rows), "the rogue chest is listed to sell with the reason", rows)
check(not any(x.startswith("Shadowcraft") and "upgrade" in x.lower() for x in rows), "and is never an upgrade", rows)
done("restrict_test")
