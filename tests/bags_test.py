"""Bag check: upgrades, sell list and the Sell junk button."""

from wowenv import runtime, source

L = runtime("ui")
L.execute("UISpecialFrames={}")
L.execute(source("DruidKit/DruidKit_Style.lua"))
L.execute(source("DruidKit/DruidKit_Bags.lua"))
L.execute(r"""
ev=frames[1]; ev.on_OnEvent(ev,"PLAYER_LOGIN")
DruidKit_ToggleBags()
texts={} for _,f in ipairs(allfs) do if f.text~="" then texts[#texts+1]=f.text end end
ev.on_OnEvent(ev,"MERCHANT_SHOW")
sb=nil for _,f in ipairs(frames) do if f.text=="Sell junk" then sb=f end end
sb.on_OnClick()
""")
g = L.globals()
for t in g.texts.values():
    print("ROW:", t)
for p in g.printed.values():
    print("PRINT:", p)
print("sold", g.sold)

from expect import check, done

rows = list(g.texts.values())
check(g.sold == 1, "Sell junk sells exactly the one grey item", g.sold)
check(any("Chain Vest" in r for r in rows), "mail armour is listed to sell")
check(any("Druids can't use this" in r for r in rows), "reason given for unusable gear")
done("bags_test")
