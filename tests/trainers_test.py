"""Trainer pins on the world map and minimap, and turning them off."""

from wowenv import runtime, source

L = runtime("map")
L.execute(source("DruidKit/DruidKit_Trainers.lua"))
L.execute(r"""
ev=frames[1]; ev.on_OnEvent(ev,"PLAYER_LOGIN")
CUR=1438; PROV:RefreshAllData()
nT=#acquired
ev.on_OnUpdate(ev,1)
shownMM={} for i=2,#frames do local f=frames[i] if f.shown and f.data then shownMM[#shownMM+1]=f.data.name.." "..string.format("%.1f,%.1f",f.pt[1],f.pt[2]) end end
ev.on_OnEvent(ev,"TRAINER_SHOW")
fix=DruidKitDB.trainerFix.Zarrin
DruidKit_TrainersCommand("off"); CUR=1438; PROV:RefreshAllData(); nOff=#acquired
""")
g = L.globals()
print("teldrassil pins incl darnassus:", g.nT)
print("minimap:", list(g.shownMM.values()))
print("fix:", g.fix.map, g.fix.x, g.fix.y, "off pins:", g.nOff, list(g.printed.values()))

from expect import check, done

check(g.nT > 0, "trainer pins drawn on the Teldrassil map", g.nT)
check(g.nOff == 0, "/dk trainers off removes the pins", g.nOff)
done("trainers_test")
