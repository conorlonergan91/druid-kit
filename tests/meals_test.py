"""Food and drink: keep the best 2 usable stacks of each (plus 1 for later); the rest is listed to sell or drop."""

from expect import check, done
from wowenv import runtime, source

L = runtime("ui")
L.execute(r"""
function UnitLevel() return 18 end
ITEMS.bread1={"Tough Hunk of Bread","bread1",1,5,1,"","",20,"",1,1,0,5}
ITEMS.bread2={"Freshly Baked Bread","bread2",1,15,5,"","",20,"",1,5,0,5}
ITEMS.bread3={"Moist Cornbread","bread3",1,25,15,"","",20,"",1,10,0,5}
ITEMS.meat={"Mutton Chop","meat",1,25,15,"","",20,"",1,12,0,5}
ITEMS.water1={"Refreshing Spring Water","water1",1,5,1,"","",20,"",1,1,0,5}
ITEMS.water2={"Ice Cold Milk","water2",1,15,5,"","",20,"",1,6,0,5}
ITEMS.later={"Melon Juice","later",1,35,25,"","",20,"",1,20,0,5}
DRINK={water1=true,water2=true,later=true}
function GetItemSpell(l) l = KEY(l); return DRINK[l] and "Drink" or "Food" end
BAG={[0]={"bread1","bread2","bread3","meat","water1","water2","later"}}
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
check(any("20c" in x for x in spare) and any("100c" in x for x in spare), "the two worst food stacks are spare", spare)
check(not any("120c" in x or "200c" in x for x in spare), "the two best food stacks are kept", spare)
check(not any("spare drink" in x.lower() for x in spare), "2 usable drinks kept, plus one for later", spare)
done("meals_test")
