"""Can you wield it? An untrained weapon type (Two-Handed Maces) or any red tooltip line means: not an upgrade,
sell it, and say why. Polearms count as druid weapons in Forever."""
from wowenv import runtime, source
from expect import check, done

L = runtime("ui")
L.execute("UISpecialFrames={}")
L.execute(source("DruidKit/DruidKit_Style.lua"))
L.execute(r"""
ITEMS.hammer = {"Smite's Mighty Hammer","hammer",3,24,18,"","",1,"INVTYPE_2HWEAPON",1,11300,2,5,1}
STATS.hammer = {ITEM_MOD_STRENGTH_SHORT=11, ITEM_MOD_AGILITY_SHORT=4, ITEM_MOD_DAMAGE_PER_SECOND_SHORT=20}
ITEMS.staff = {"Medicine Staff","staff",2,22,17,"","",1,"INVTYPE_2HWEAPON",1,900,2,10,2}
STATS.staff = {ITEM_MOD_STAMINA_SHORT=5, ITEM_MOD_STRENGTH_SHORT=5, ITEM_MOD_DAMAGE_PER_SECOND_SHORT=14}
ITEMS.redboots = {"Odd Boots","redboots",2,22,17,"","",1,"INVTYPE_FEET",1,500,4,2,2}
STATS.redboots = {ITEM_MOD_STAMINA_SHORT=8, RESISTANCE0_NAME=60}
KNOWN = { [227] = true, [1180] = true }          -- Staves, Daggers only
function IsPlayerSpell(id) return KNOWN[id] == true end
C_TooltipInfo = { GetHyperlink = function(l)
  if l == "redboots" then return { lines = { { leftText = "Odd Boots" }, { leftText = "Classes: Druid" },
    { leftText = "Requires Rogue", leftColor = { r = 1, g = 0.13, b = 0.13 } } } } end
  if l == "hammer" then return { lines = { { leftText = "Smite's Mighty Hammer" }, { leftText = "Two-Hand", rightText = "Mace", rightColor = { r = 1, g = 0.13, b = 0.13 } } } } end
  return { lines = {} } end }
""")
L.execute(source("DruidKit/DruidKit_Bags.lua"))
L.execute(r"""
R = { DruidKit_CantWield("hammer"), DruidKit_CantWield("staff"), DruidKit_CantWield("redboots") }
""")
r = list(L.globals().R.values()) if L.globals().R else []
g = L.globals()
print(g.R[1], "|", g.R[2], "|", g.R[3])
check(g.R[1] and "Two-Handed Maces" in g.R[1], "an untrained weapon type is not wieldable, with the skill named", g.R[1])
check(g.R[2] is None, "a staff (trained) is fine", g.R[2])
check(g.R[3] and "Requires Rogue" in g.R[3], "a red tooltip line blocks the item", g.R[3])
done("wield_test")
