"""Navigation: only the route's own waypoints tick route steps, unknown zones don't fall back to your map,
rotating minimap pins turn the right way, and map corners are worked out once per map."""

from lupa.lua51 import LuaRuntime

from expect import check, done
from wowenv import source

MOCKS = r"""
printed={}
function print(...) local t={} for i=1,select('#',...) do t[#t+1]=tostring(select(i,...)) end printed[#printed+1]=table.concat(t," ") end
local function mkobj()
  local o={shown=false,text=""}
  return setmetatable(o,{__index=function(t,k)
    if k=="Show" then return function(s) s.shown=true end end
    if k=="Hide" then return function(s) s.shown=false end end
    if k=="IsShown" or k=="IsVisible" then return function(s) return s.shown end end
    if k=="SetText" then return function(s,v) s.text=v end end
    if k=="GetText" then return function(s) return s.text end end
    if k=="GetStringHeight" then return function() return 10 end end
    if k=="SetPoint" then return function(s,a,rel,b,x,y) s.x, s.y = x, y end end
    if k=="CreateTexture" or k=="CreateFontString" then return function() return mkobj() end end
    if k=="SetScript" then return function(s,e,f) s["on_"..e]=f end end
    if k=="RegisterEvent" then return function(s,e) s.events=s.events or {}; s.events[e]=true end end
    if type(k)=="string" and k:match("^%u") then return function() end end
  end})
end
frames={}
function CreateFrame(kind, name) local f=mkobj(); frames[#frames+1]=f; if name then _G[name]=f end; return f end
UIParent=mkobj(); GameTooltip=mkobj(); WorldMapFrame=nil
C_Timer={After=function(d,f) f() end}
SlashCmdList={}
function CreateVector2D(x,y) return {x=x,y=y,GetXY=function(s) return s.x,s.y end} end
CORNERS=0
C_Map={GetWorldPosFromMapPos=function(m,v)
    if m ~= 1 then return nil end
    if (v.x==0 or v.x==1) and (v.y==0 or v.y==1) then CORNERS=CORNERS+1 end
    return 0, CreateVector2D(-v.y*500, -v.x*1000) end,
 GetBestMapForUnit=function() return 1 end, GetPlayerMapPosition=function() return CreateVector2D(PX,PY) end,
 GetMapInfo=function(id) return id == 1 and {name="Westfall",mapType=3} or nil end}
PX,PY=0.5,0.5; FACE=0
function GetPlayerFacing() return FACE end
function IsControlKeyDown() return false end
function UnitLevel() return 10 end
function wipe(t) for k in pairs(t) do t[k] = nil end return t end
"""

# 1: a /way waypoint (or trainer pin, map click, guide Go) doesn't tick the route's goto step; the route's own does.
L = LuaRuntime(unpack_returned_tuples=True)
L.execute(MOCKS)
L.execute(r"""
DruidKitRoute = { id = "n", sections = { { title = "S", steps = {
  { ["do"] = "goto", text = "Walk to the tower", to = "Nowhere", at = { "Westfall", 60, 50 } },
  { ["do"] = "note", text = "then" },
} } } }
""")
L.execute(source("DruidKit/DruidKit_Trainers.lua"))
L.execute(source("DruidKit/DruidKit_Steps.lua"))
L.execute(r"""
for _, f in ipairs(frames) do if f.events and f.events.QUEST_DETAIL then ev = f end end
ev.on_OnEvent(ev, "PLAYER_LOGIN")
R = {}
R[1] = tostring(DruidKit_NavTarget().owner)
SlashCmdList.DRUIDKITWAY("Westfall 40 50 Rumi")
PX = 0.4; DruidKit_NavUpdate()
R[2] = DruidKitDB.routeStep
R[3] = DruidKit_NavTarget() and DruidKit_NavTarget().label or ""
PX = 0.6; DruidKit_NavUpdate()
R[4] = DruidKitDB.routeStep
""")
r = list(L.globals().R.values())
check(r[0] == "route", "the route's arrow is marked as the route's", r[0])
check(r[1] == 1, "arriving at a /way waypoint doesn't tick the goto step", r[1])
check("Walk to the tower" in str(r[2]), "the route arrow comes back after it", r[2])
check(r[3] == 2, "arriving at the route's own spot ticks the step", r[3])

# 2: an unknown zone name isn't silently your current map; no zone still is.
L = LuaRuntime(unpack_returned_tuples=True)
L.execute(MOCKS)
L.execute(source("DruidKit/DruidKit_Trainers.lua"))
L.execute(r"""
bad = DruidKit_GoTo("Atlantis", 50, 50, "Lost")
badSaid = printed[#printed]
good = DruidKit_GoTo(nil, 50, 40, "Here")
""")
g = L.globals()
check(
    g.bad is False and "can't find the map for Atlantis" in g.badSaid, "unknown zone: no waypoint, says so", g.badSaid
)
check(g.good is True, "no zone: your current map", g.good)

# 7: map corners are worked out once per map, not on every arrow update.
L.execute(r"""
c0 = CORNERS
for i = 1, 20 do DruidKit_NavUpdate() end
c1 = CORNERS
""")
check(g.c1 == g.c0, "arrow updates reuse the map's corners", (g.c0, g.c1))

# 9: on a rotating minimap, a pin north of you shows on the right when you face west.
L = LuaRuntime(unpack_returned_tuples=True)
L.execute(MOCKS)
L.execute(r"""
Minimap = CreateFrame()
Minimap.shown = true
Minimap.GetZoom = function() return 0 end
Minimap.GetWidth = function() return 140 end
Minimap.GetFrameLevel = function() return 1 end
function GetCVar(k) return k == "rotateMinimap" and "1" or nil end
function UnitPosition() return -250, -500, 0, 0 end
DruidKitDB = { places = { { cat = "bank", name = "Bank", map = 1, x = 0.5, y = 0.4 } } }
""")
L.execute(source("DruidKit/DruidKit_Trainers.lua"))
L.execute(r"""
ev = frames[2]
ev.on_OnEvent(ev, "PLAYER_LOGIN")
FACE = math.pi / 2
ev.on_OnUpdate(ev, 0.2)
pin = frames[#frames]
""")
pin = L.globals().pin
check(pin.x is not None and pin.x > 10 and abs(pin.y) < 1, "facing west, north is to your right", (pin.x, pin.y))
done("core_nav_test")
