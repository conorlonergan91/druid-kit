"""Go to window, waypoints and learned places (bank found via the modern interaction event)."""

from wowenv import runtime, source

L = runtime("map")
L.execute(r"""
Enum={PlayerInteractionType={Banker=8,Auctioneer=21,TaxiNode=5,MailInfo=17,Binder=24}}
UiMapPoint={CreateFromCoordinates=function(m,x,y) return {m=m,x=x,y=y} end}
C_Map.SetUserWaypoint=function(pt) WP=pt end
C_Map.CanSetUserWaypointOnMap=function() return true end
C_SuperTrack={SetSuperTrackedUserWaypoint=function(v) ST=v end}
skills={{"Alchemy",false},{"Cooking",false}}
function GetNumSkillLines() return #skills end
function GetSkillLineInfo(i) return skills[i][1], skills[i][2] end
C_Container={GetContainerNumSlots=function() return 1 end, GetContainerItemInfo=function() return {hyperlink="|Hitem:1|h[Waylaid Crate: Apprentice Herbs]|h"} end}
rows={}
DruidKitStyle={window=function() local f=CreateFrame(); f.IsShown=function(s) return s.shown end; return f end,
  begin=function() rows={} end, header=function(f,t) rows[#rows+1]="H "..t end,
  item=function(f,l,i,q,t,d,b,fn) rows[#rows+1]="I "..t; GO=GO or fn end,
  note=function(f,t) rows[#rows+1]="N "..t end, finish=function() end}
""")
L.execute(source("DruidKit/DruidKit_Trainers.lua"))
L.execute(r"""
ev=frames[1]; ev.on_OnEvent(ev,"PLAYER_LOGIN"); WorldMapFrame.IsShown=function() return false end
UnitName=function() return "Newton Burnside" end
ev.on_OnEvent(ev,"PLAYER_INTERACTION_MANAGER_FRAME_SHOW", 8)
DruidKit_ToggleGo()
if GO then GO() end
""")
g = L.globals()
rows = list(g.rows.values())
ok = (
    g.DruidKitDB.places[1].cat == "bank"
    and any("Bank: Newton Burnside" in r for r in rows)
    and any("Druid trainer" in r for r in rows)
    and any("Alchemy" in r for r in rows)
    and any("Waylaid" in r for r in rows)
    and g.WP is not None
    and g.ST is True
)
print("goto_test", "OK" if ok else "FAIL")
if not ok:
    print(rows, g.WP, list(g.printed.values()))
