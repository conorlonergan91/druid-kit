"""Recipes: learn only when your skill is high enough; bank if not yet; sell if known or no skill."""

from expect import check, done
from wowenv import runtime, source

L = runtime("ui")
L.execute(r"""
ITEMS.r1={"Recipe: Westfall Stew","r1",1,15,0,"","",1,"",1,100,9,5}
ITEMS.r2={"Recipe: Goretusk Liver Pie","r2",1,10,0,"","",1,"",1,100,9,5}
ITEMS.r3={"Recipe: Known Thing","r3",1,10,0,"","",1,"",1,100,9,5}
ITEMS.r4={"Recipe: Gem Thing","r4",1,10,0,"","",1,"",1,100,9,5}
TIPS={r1={"Recipe: Westfall Stew","Requires Cooking (75)"}, r2={"Recipe: Goretusk Liver Pie","Requires Cooking (50)"},
      r3={"Recipe: Known Thing","Requires Cooking (1)","Already known"}, r4={"Recipe: Gem Thing","Requires Jewelcrafting (1)"}}
C_TooltipInfo={GetHyperlink=function(l) local t={} for _,x in ipairs(TIPS[l] or {}) do t[#t+1]={leftText=x} end return {lines=t} end}
SKILLS={{"Professions",true,0,0},{"Cooking",false,0,52},{"Herbalism",false,0,86}}
function GetNumSkillLines() return #SKILLS end
function GetSkillLineInfo(i) local s=SKILLS[i]; return s[1],s[2],s[3],s[4] end
BAG={[0]={"r1","r2","r3","r4"}}
UISpecialFrames={}
""")
L.execute(source("DruidKit/DruidKit_Style.lua"))
L.execute(source("DruidKit/DruidKit_Bags.lua"))
L.execute(r"""
ev=frames[1]; ev.on_OnEvent(ev,"PLAYER_LOGIN")
DruidKit_ToggleBags()
texts={} for _,f in ipairs(allfs) do if f.text~="" then texts[#texts+1]=f.text end end
""")
t = "\n".join(L.eval("texts").values()).lower()
check("learn at cooking 75 (you're 52)" in t, "Westfall Stew needs Cooking 75: bank it", "")
check(t.count("right-click to learn it") == 1, "only the Cooking 50 recipe says learn", "")
check("already know this recipe" in t, "known recipe offered for sale", "")
check("needs jewelcrafting" in t, "recipe for a skill you don't have offered for sale", "")
done("recipe_test")
