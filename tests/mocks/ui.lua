-- Mocked WoW UI and item API shared by the bag, bank, bars and guide tests.
printed={}
function print(...) local t={} for i=1,select('#',...) do t[#t+1]=tostring(select(i,...)) end printed[#printed+1]=table.concat(t," ") end
local function mkobj()
  local o={shown=false,text=""}
  return setmetatable(o,{__index=function(t,k)
    if type(k)=="string" and k:match("^%u") then
      if k=="Show" then return function(s) s.shown=true end end
      if k=="Hide" then return function(s) s.shown=false end end
      if k=="IsShown" then return function(s) return s.shown end end
      if k=="SetText" then return function(s,v) s.text=v end end
      if k=="CreateTexture" or k=="CreateFontString" then return function() local x=mkobj(); allfs[#allfs+1]=x; return x end end
      if k=="SetScript" then return function(s,e,f) s["on_"..e]=f end end
      if k=="GetStringHeight" then return function() return 10 end end
      if k=="HasScript" then return function() return true end end
      return function() end
    end end})
end
allfs={}; frames={}
function CreateFrame() local f=mkobj(); frames[#frames+1]=f; return f end
UIParent=mkobj(); GameTooltip=mkobj(); MerchantFrame=mkobj()
C_Timer={After=function(d,f) f() end}
function InCombatLockdown() return false end
StaticPopupDialogs = StaticPopupDialogs or {}; StaticPopup_Show = StaticPopup_Show or function(n) print("POPUP "..n) end; ReloadUI = function() end
GetShapeshiftForm = GetShapeshiftForm or function() return 0 end
function UnitLevel() return 12 end
-- items: name,link,quality,ilvl,minLevel,type,sub,stack,equipLoc,icon,price,classID,subID
-- ITEMS/BAG/EQ use short keys; the API hands out real-shaped links (LINK) with distinct item IDs, KEY maps back.
local ids, keys, nextID = {}, {}, 100
function LINK(k)
  if type(k) ~= "string" or not ITEMS[k] then return k end
  if not ids[k] then nextID = nextID + 1; ids[k] = nextID; keys[nextID] = k end
  return ("|cffffffff|Hitem:%d::::::::|h[%s]|h|r"):format(ids[k], ITEMS[k][1])
end
function KEY(l)
  local id = type(l) == "string" and tonumber(l:match("item:(%d+)"))
  if id then return keys[id] end
  return l
end
function ITEMID(k) LINK(k); return ids[k] end
ITEMS={
 ["robe"]={"Sleeping Robes","robe",2,15,10,"","",1,"INVTYPE_ROBE",1,300,4,1},
 ["oldchest"]={"Old Tunic","oldchest",1,5,1,"","",1,"INVTYPE_CHEST",1,10,4,2},
 ["mail"]={"Chain Vest","mail",1,12,8,"","",1,"INVTYPE_CHEST",1,150,4,3},
 ["grey"]={"Broken Tooth","grey",0,5,0,"","",20,"",1,7,15,0},
 ["herb"]={"Peacebloom","herb",1,5,0,"","",20,"",1,4,7,9},
 ["note"]={"Torn Note","note",1,5,0,"","",1,"",1,0,12,0},
 ["pole"]={"Fishing Pole","pole",1,5,0,"","",1,"INVTYPE_2HWEAPON",1,5,2,20},
 ["boots"]={"Worn Boots","boots",1,5,1,"","",1,"INVTYPE_FEET",1,20,4,2},
}
STATS={robe={ITEM_MOD_STAMINA_SHORT=4,ITEM_MOD_INTELLECT_SHORT=3,RESISTANCE0_NAME=30},
 oldchest={RESISTANCE0_NAME=20}, mail={ITEM_MOD_STAMINA_SHORT=2,RESISTANCE0_NAME=80},
 boots={RESISTANCE0_NAME=10}, newboots={RESISTANCE0_NAME=40}}
local function itemInfo(l)
  local k = KEY(l); local i = ITEMS[k]
  if i then
    local r = { (table.unpack or unpack)(i, 1, 14) }; r[2] = LINK(k)
    return (table.unpack or unpack)(r, 1, 14)
  end
end
C_Item={GetItemInfo=itemInfo,
        GetItemStats=function(l) return STATS[KEY(l)] end, EquipItemByName=function(l) equipped=KEY(l) end}
EQ={[5]="oldchest",[8]="newboots"}
ITEMS.newboots={"Good Boots","newboots",1,10,5,"","",1,"INVTYPE_FEET",1,30,4,2}
function GetInventoryItemLink(_,s) return LINK(EQ[s]) end
BAG={[0]={"robe","mail","grey","herb","note","boots","pole"}}
C_Container={GetContainerNumSlots=function(b) return b==0 and 7 or 0 end,
 GetContainerItemInfo=function(b,s) local l=BAG[b] and BAG[b][s]; if l then return {hyperlink=LINK(l),stackCount=ITEMS[l][8],quality=ITEMS[l][3],itemID=ITEMID(l)} end end,
 GetContainerItemQuestInfo=function(b,s) local l=BAG[b][s]; if l=="note" then return {isQuestItem=true,questID=99,isActive=false} end return {} end,
 UseContainerItem=function(b,s) sold=(sold or 0)+1 end}
function GetCoinTextureString(c) return c.."c" end
