"""Bank check: what to take out and put in, plus the bag list beside it."""

from wowenv import runtime, source

L = runtime("ui")
L.execute(r"""
ITEMS.silverleaf={"Silverleaf","silverleaf",1,5,0,"","",20,"",1,4,7,9}
ITEMS.potion={"Minor Healing Potion","potion",1,5,1,"","",5,"",1,5,0,1}
ITEMS.pole2={"Strong Fishing Pole","pole2",1,10,10,"","",1,"INVTYPE_2HWEAPON",1,200,2,20}
BAG[0]={"robe","grey","herb","silverleaf","pole","pole2"}
BAG[-1]={"potion","silverleaf"}
local base=C_Container.GetContainerNumSlots
C_Container.GetContainerNumSlots=function(b) if b==0 then return 7 elseif b==-1 then return 3 end return 0 end
C_Container.GetContainerItemQuestInfo=function() return {} end
moved={}
C_Container.UseContainerItem=function(b,s) moved[#moved+1]=b..":"..s end
C_Container.PickupContainerItem=function(b,s) picked=b..':'..s end
BankFrame={IsShown=function() return false end}
GetNumTradeSkills=function() return 2 end
ITEMS.meat={"Strider Meat","meat",1,5,0,"","",10,"",1,4,7,8}
BAG[0][#BAG[0]+1]="meat"; BAG[-1][#BAG[-1]+1]="meat"
GetTime=function() return 100 end
C_QuestLog={GetNumQuestLogEntries=function() return 1 end, GetInfo=function() return {questID=5} end, GetQuestObjectives=function() return {{text="1/5 Strider Meat"}} end}
GetTradeSkillLine=function() return "Alchemy" end
GetTradeSkillInfo=function(i) if i==1 then return "Minor Healing Potion","medium" else return "Elixir of Minor Defense","trivial" end end
GetTradeSkillNumReagents=function(i) return 1 end
GetTradeSkillReagentInfo=function(i,j) return i==1 and "Silverleaf" or "Peacebloom" end
""")
L.execute("UISpecialFrames={}")
L.execute(source("DruidKit/DruidKit_Style.lua"))
L.execute(source("DruidKit/DruidKit_Bags.lua"))
L.execute(source("DruidKit/DruidKit_Bank.lua"))
L.execute(r"""
for _,f in ipairs(frames) do if f.on_OnEvent then f.on_OnEvent(f,"PLAYER_LOGIN") end end
for _,f in ipairs(frames) do if f.on_OnEvent then f.on_OnEvent(f,"TRADE_SKILL_SHOW") end end
allfs={}
for _,f in ipairs(frames) do if f.on_OnEvent then f.on_OnEvent(f,"BANKFRAME_OPENED") end end
texts={} for _,f in ipairs(allfs) do if f.text~="" then texts[#texts+1]=f.text end end
DruidKit_ToggleBags()
bt={} for _,f in ipairs(allfs) do if f.text~="" then bt[#bt+1]=f.text end end
""")
g = L.globals()
for t in g.texts.values():
    print("BANK:", t)
[print("BAG:", t) for t in g.bt.values()]

from expect import check, done

bag = list(g.bt.values())
check(any("Broken Tooth" in r for r in bag), "grey junk offered to sell")
check(any("better fishing pole" in r for r in bag), "spare fishing pole offered to sell")
done("bank_test")
