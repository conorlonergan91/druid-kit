"""Dungeon packing: with /dk pack (or a route step with pack), the bank check offers every non-essential item to the
bank and keeps hearthstone, potions, food, bandages, quest items and gear."""
from wowenv import runtime, source
from expect import check, done

L = runtime("ui")
L.execute(r"""
ITEMS.silverleaf={"Silverleaf","silverleaf",1,5,0,"","",20,"",1,4,7,9}
ITEMS.potion={"Minor Healing Potion","potion",1,5,1,"","",5,"",1,5,0,1}
ITEMS.hearth={"Hearthstone","hearth",1,1,0,"","",1,"",1,0,15,0}
ITEMS.linen={"Linen Cloth","linen",1,5,0,"","",20,"",1,13,7,5}
ITEMS.recipe={"Recipe: Breakfast Omelette","recipe",1,20,0,"","",1,"",1,50,9,5}
ITEMS.bandage={"Wool Bandage","bandage",1,20,0,"","",20,"",1,30,0,7}
BAG[0]={"robe","silverleaf","potion","hearth","linen","recipe","bandage","pole"}
C_Container.GetContainerNumSlots=function(b) if b==0 then return 8 elseif b==-1 then return 4 end return 0 end
BAG[-1]={}
C_Container.GetContainerItemQuestInfo=function() return {} end
moved={}
C_Container.UseContainerItem=function(b,s) moved[#moved+1]=BAG[b][s] end
BankFrame={IsShown=function() return false end}
GetTime=function() return 100 end
""")
L.execute("UISpecialFrames={}")
L.execute(source("DruidKit/DruidKit_Style.lua"))
L.execute(source("DruidKit/DruidKit_Bags.lua"))
L.execute(source("DruidKit/DruidKit_Bank.lua"))
L.execute(r"""
for _,f in ipairs(frames) do if f.on_OnEvent then f.on_OnEvent(f,"PLAYER_LOGIN") end end
DruidKit_HelperCommand("pack", "on")
for _,f in ipairs(frames) do if f.on_OnEvent then f.on_OnEvent(f,"BANKFRAME_OPENED") end end
-- press "Store all"
for _,f in ipairs(frames) do if f.text == "Store all" and f.on_OnClick then f.on_OnClick() end end
""")
moved = list(L.globals().moved.values())
print("stored:", moved)
check("silverleaf" in moved and "linen" in moved and "recipe" in moved and "pole" in moved, "herbs, cloth, recipes, fishing pole go to the bank", moved)
check(not any(x in moved for x in ("potion", "hearth", "bandage", "robe")), "potions, hearthstone, bandages and gear stay", moved)
done("pack_test")
