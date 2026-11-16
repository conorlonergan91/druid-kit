"""Navigation arrow: direction words, distance in yards, arrival and /way parsing."""

from lupa.lua51 import LuaRuntime

from wowenv import source

L = LuaRuntime(unpack_returned_tuples=True)
L.execute(r"""
printed={}
function print(...) local t={} for i=1,select('#',...) do t[#t+1]=tostring(select(i,...)) end printed[#printed+1]=table.concat(t," ") end
local function mkobj()
  local o={shown=false,text="",rot=0}
  return setmetatable(o,{__index=function(t,k)
    if k=="Show" then return function(s) s.shown=true end end
    if k=="Hide" then return function(s) s.shown=false end end
    if k=="IsShown" then return function(s) return s.shown end end
    if k=="SetText" then return function(s,v) s.text=v end end
    if k=="SetRotation" then return function(s,v) s.rot=v end end
    if k=="CreateTexture" or k=="CreateFontString" then return function() return mkobj() end end
    if k=="SetScript" then return function(s,e,f) s["on_"..e]=f end end
    if k=="RegisterEvent" then return function(s,e) end end
    if type(k)=="string" and k:match("^%u") then return function() end end
  end})
end
frames={}
function CreateFrame() local f=mkobj(); frames[#frames+1]=f; return f end
UIParent=mkobj(); GameTooltip=mkobj(); WorldMapFrame=nil
C_Timer={After=function(d,f) f() end}
SlashCmdList={}
function CreateVector2D(x,y) return {x=x,y=y,GetXY=function(s) return s.x,s.y end} end
-- map 1: 1000 x 500 yards, world = (north=-y*500, west=-x*1000)
C_Map={GetWorldPosFromMapPos=function(m,v) return 0, CreateVector2D(-v.y*500, -v.x*1000) end,
 GetMapPosFromWorldPos=function(c,w,m) return c, CreateVector2D(-w.y/1000, -w.x/500) end,
 GetBestMapForUnit=function() return 1 end, GetPlayerMapPosition=function() return CreateVector2D(PX,PY) end,
 GetMapInfo=function(id) return {name="Westfall",mapType=3} end}
PX,PY=0.5,0.5; FACE=0
function GetPlayerFacing() return FACE end
function IsControlKeyDown() return false end
""")
L.execute(source("DruidKit/DruidKit_Trainers.lua"))
L.execute(r"""
r={}
DruidKit_NavTo(1,0.4,0.5,"West spot"); r[#r+1]=DruidKitArrow and "" or ""
local a=_G.DruidKitArrow
""")
g = L.globals()
L.execute(r"""
for _,f in ipairs(frames) do if f.info then A=f end end
r={}
r[#r+1]="west, facing north: "..A.info.text
FACE=math.pi/2; DruidKit_NavUpdate(); r[#r+1]="west, facing west: "..A.info.text
DruidKit_NavTo(1,0.5,0.4,"North spot"); FACE=0; DruidKit_NavUpdate(); r[#r+1]="north 50yd: "..A.info.text
DruidKit_NavTo(1,0.6,0.5,"East"); DruidKit_NavUpdate(); r[#r+1]="east: "..A.info.text.." rot "..string.format("%.2f",A.tex.rot)
PX=0.6; DruidKit_NavUpdate(); r[#r+1]="arrived shown="..tostring(A.shown)
SlashCmdList.DRUIDKITWAY("Westfall 52.7 53.8 Rumi book"); r[#r+1]="way: "..A.name.text
""")
for x in g.r.values():
    print(x)
for p in g.printed.values():
    print("PRINT", p)

from expect import check, done

r = list(g.r.values())
check("turn left" in r[0], "target to the west while facing north: turn left", r[0])
check("straight ahead" in r[1], "facing the target: straight ahead", r[1])
check("50 yards" in r[2], "distance uses the map's real size in yards", r[2])
check("turn right" in r[3], "target to the east: turn right", r[3])
check(r[4] == "arrived shown=false", "arrow hides on arrival", r[4])
check("Westfall 52.7, 53.8" in r[5], "/way parses zone and coordinates", r[5])
done("nav_test")
