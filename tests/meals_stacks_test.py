"""Food and drink are counted by item, not by stack: several stacks of the drink you keep are all kept."""

from expect import check, done
from wowenv import runtime, source

L = runtime("ui")
L.execute(r"""
function UnitLevel() return 24 end
ITEMS.milkA={"Ice Cold Milk","milkA",1,15,5,"","",20,"",1,6,0,5}
ITEMS.milkB={"Ice Cold Milk","milkB",1,15,5,"","",20,"",1,6,0,5}
ITEMS.water1={"Refreshing Spring Water","water1",1,5,1,"","",20,"",1,1,0,5}
ITEMS.water0={"Fresh Water","water0",1,1,1,"","",20,"",1,1,0,5}
DRINK={milkA=true,milkB=true,water1=true,water0=true}
function GetItemSpell(l) l = KEY(l); return DRINK[l] and "Drink" or "Food" end
BAG={[0]={"milkA","milkB","water1","water0"}}
UISpecialFrames={}
""")
L.execute(source("DruidKit/DruidKit_Style.lua"))
L.execute(source("DruidKit/DruidKit_Bags.lua"))
L.execute(r"""
ev=frames[1]; ev.on_OnEvent(ev,"PLAYER_LOGIN")
DruidKit_ToggleBags()
texts={} for _,f in ipairs(allfs) do if f.text~="" then texts[#texts+1]=f.text end end
""")
lines = list(L.eval("texts").values())
spare = [x for x in lines if "spare" in x.lower()]
print(spare)
check(len(spare) == 1, "both Ice Cold Milk stacks kept (one drink), only the worst other drink is spare", spare)
done("meals_stacks_test")
