"""Quest items and library books are never sold; Sell junk skips them."""

from wowenv import runtime, source

L = runtime("ui")
L.execute("UISpecialFrames={}")
L.execute(source("DruidKit/DruidKit_Style.lua"))
L.execute(source("DruidKit/DruidKit_Bags.lua"))

L.execute(r"""
ITEMS.book={"Rumi of Gnomeregan: The Collected Works","book",0,20,0,"","",1,"",1,25,15,0}
ITEMS.band={"Red Leather Bandana","band",0,5,0,"","",20,"",1,5,15,0,0}
ITEMS.future={"Future Vest","future",2,20,15,"","",1,"INVTYPE_CHEST",1,300,4,2,1}; STATS.future={ITEM_MOD_STAMINA_SHORT=8,RESISTANCE0_NAME=70}
BAG={[0]={"robe","mail","grey","herb","note","boots","pole","book","band","future"}}
C_Container.GetContainerNumSlots=function(b) return b==0 and 10 or 0 end
C_QuestLog={GetNumQuestLogEntries=function() return 1 end, GetInfo=function() return {questID=5} end,
  GetQuestObjectives=function() return {{text="4/15 Red Leather Bandanas"}} end}
function GetTime() return 1000 end
ev=frames[1]; ev.on_OnEvent(ev,"PLAYER_LOGIN")
MerchantFrame.shown=true
DruidKit_ToggleBags()
texts={} for _,f in ipairs(allfs) do if f.text~="" then texts[#texts+1]=f.text end end
sold=0
ev.on_OnEvent(ev,"MERCHANT_SHOW")
for _,f in ipairs(frames) do if f.text=="Sell junk" then f.on_OnClick() end end
""")
g = L.globals()
for x in g.texts.values():
    print("ROW:", x)
print("sold", g.sold)

from expect import check, done

rows = list(g.texts.values())
sell_rows = rows[rows.index("Sell at a vendor") :] if "Sell at a vendor" in rows else rows
check(not any("Rumi of Gnomeregan" in r for r in sell_rows), "library book never offered to sell")
check(
    "Rumi of Gnomeregan: The Collected Works" in rows and any("Library book" in r for r in rows),
    "library book listed under Bank these",
)
check(not any("Red Leather Bandana" in r for r in sell_rows), "grey quest item never offered to sell")
check(g.sold == 1, "Sell junk skips protected greys", g.sold)
done("protect_test")
