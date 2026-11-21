"""Healing mode with no saved set wears the best healing pieces from the bags (Bags API bestSet)."""
from expect import check, done
from wowenv import runtime, source

L = runtime("ui")
L.execute(r"""
function UnitLevel() return 24 end
UISpecialFrames = {}
-- worn: feral gear
ITEMS.harpoon={"Impaling Harpoon","harpoon",2,20,17,"","",1,"INVTYPE_2HWEAPON",1,900,2,6}
ITEMS.direlegs={"Direhammer Leggings","direlegs",3,18,13,"","",1,"INVTYPE_LEGS",1,600,4,2}
ITEMS.magicsh={"Superior Shoulders of Magic","magicsh",2,27,22,"","",1,"INVTYPE_SHOULDER",1,1200,4,2}
-- in the bags: healing gear and a cloth mantle that is worse than the worn shoulders
ITEMS.stave={"Golemheart Stave","stave",3,18,13,"","",1,"INVTYPE_2HWEAPON",1,1600,2,10}
ITEMS.dreamer={"Dreamer's Leggings","dreamer",2,22,0,"","",1,"INVTYPE_LEGS",1,900,4,2}
ITEMS.mantle={"Bright Mantle","mantle",2,26,21,"","",1,"INVTYPE_SHOULDER",1,900,4,1}
ITEMS.tunic={"Burnished Tunic","tunic",2,21,16,"","",1,"INVTYPE_CHEST",1,1000,4,3}
STATS.harpoon={ITEM_MOD_AGILITY_SHORT=9,ITEM_MOD_INTELLECT_SHORT=5,ITEM_MOD_DAMAGE_PER_SECOND_SHORT=19}
STATS.direlegs={ITEM_MOD_STAMINA_SHORT=7,ITEM_MOD_AGILITY_SHORT=4,RESISTANCE0_NAME=72}
STATS.magicsh={ITEM_MOD_SPELL_POWER_SHORT=8,RESISTANCE0_NAME=67}
STATS.stave={ITEM_MOD_SPELL_POWER_SHORT=18,ITEM_MOD_DAMAGE_PER_SECOND_SHORT=11.9}
STATS.dreamer={ITEM_MOD_INTELLECT_SHORT=6,ITEM_MOD_SPELL_POWER_SHORT=2,RESISTANCE0_NAME=71}
STATS.mantle={ITEM_MOD_INTELLECT_SHORT=5,ITEM_MOD_SPIRIT_SHORT=4,RESISTANCE0_NAME=30}
STATS.tunic={ITEM_MOD_STRENGTH_SHORT=6,ITEM_MOD_STAMINA_SHORT=3,RESISTANCE0_NAME=171}
EQ={[16]="harpoon",[7]="direlegs",[3]="magicsh"}
BAG={[0]={"stave","dreamer","mantle","tunic"}}
C_Container.GetContainerNumSlots=function(b) return b==0 and 4 or 0 end
function IsPlayerSpell() return true end
""")
L.execute(source("DruidKit/DruidKit_Style.lua"))
L.execute(source("DruidKit/DruidKit_Bags.lua"))
L.execute(r"""
ev=frames[1]; ev.on_OnEvent(ev,"PLAYER_LOGIN")
picks = DruidKitBagsAPI.bestSet("heal")
names = {}
for _, e in ipairs(picks) do names[#names+1] = e.link end
qpicks = DruidKitBagsAPI.bestSet("quest")
qnames = {}
for _, e in ipairs(qpicks) do qnames[#qnames+1] = e.link end
""")
names = sorted(L.eval("names").values())
qnames = sorted(L.eval("qnames").values())
print(names, qnames)
check("stave" in names and "dreamer" in names, "healing: the spell power staff and the Intellect leggings", names)
check("mantle" not in names, "healing: not a cloth mantle worse than the worn spell power shoulders", names)
check("tunic" not in names, "never mail for a druid", names)
check("stave" not in qnames, "questing: the feral weapon stays", qnames)
done("bestset_test")
