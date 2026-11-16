-- Mocked world map, minimap and C_Map API for the trainer pin and Go to tests.
printed={}
function print(...) local t={} for i=1,select('#',...) do t[#t+1]=tostring(select(i,...)) end printed[#printed+1]=table.concat(t," ") end
function wipe(t) for k in pairs(t) do t[k]=nil end return t end
local function mkobj()
  local o={shown=false}
  return setmetatable(o,{__index=function(t,k)
    if type(k)=="string" and k:match("^%u") then
      if k=="Show" then return function(s) s.shown=true end end
      if k=="Hide" then return function(s) s.shown=false end end
      if k=="SetPoint" then return function(s,a,b,c,dx,dy) s.pt={dx,dy} end end
      if k=="CreateTexture" then return function() return mkobj() end end
      if k=="SetScript" then return function(s,e,f) s["on_"..e]=f end end
      if k=="GetWidth" then return function() return 140 end end
      if k=="GetZoom" then return function() return 0 end end
      if k=="IsVisible" then return function() return true end end
      if k=="GetFrameLevel" then return function() return 1 end end
      return function() end
    end end})
end
frames={}
function CreateFrame() local f=mkobj(); frames[#frames+1]=f; return f end
Minimap=mkobj()
function CreateFromMixins(...) local t={} for _,m in ipairs({...}) do for k,v in pairs(m) do t[k]=v end end return t end
MapCanvasPinMixin={}; MapCanvasDataProviderMixin={GetMap=function(s) return s.map end}
acquired={}
WorldMapFrame={AddDataProvider=function(self,p) p.map={GetMapID=function() return CUR end,
  RemoveAllPinsByTemplate=function() wipe(acquired) end,
  AcquirePin=function(_,tpl,p,x,y) acquired[#acquired+1]={p.name,x,y} end}; PROV=p end}
local names={[1438]="Teldrassil",[1457]="Darnassus",[1450]="Moonglade"}
C_Map={GetMapInfo=function(id) if names[id] then return {name=names[id], parentMapID=(id==1457 and 1438 or 1414)} end
         if id==2100 then return {name="Zephras Isle",parentMapID=1414} end end,
  GetMapChildrenInfo=function() return {{mapID=2100,name="Zephras Isle"},{mapID=1438,name="Teldrassil"}} end,
  GetWorldPosFromMapPos=function(id,v) return 1, {GetXY=function() return 10000 - v.y*1000, 5000 - v.x*1000 end} end,
  GetMapRectOnMap=function() return 0.3,0.5,0.4,0.6 end,
  GetBestMapForUnit=function() return 1438 end,
  GetPlayerMapPosition=function() return {GetXY=function() return 0.571,0.612 end} end}
function CreateVector2D(x,y) return {x=x,y=y} end
function UnitPosition() return 10000-0.607*1000, 5000-0.577*1000, 0, 1 end
function IsIndoors() return false end
function GetCVar() return "0" end
function UnitName() return "Zarrin" end
GameTooltip=mkobj()
