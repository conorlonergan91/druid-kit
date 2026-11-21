"""Smoke test: every DruidKit file loaded together (TOC order), every main event, OnUpdate, slash commands, then
the same in combat. Any Lua error fails. DK_LIVE=/path runs it on the live copies."""
import sys
sys.path.insert(0,str(__import__("pathlib").Path(__file__).resolve().parent))
from wowenv import runtime, source
from pathlib import Path
import os
Q=Path(os.environ.get('DK_LIVE') or (Path(__file__).resolve().parent.parent/'DruidKit'))
L = runtime("ui")
L.execute(r"""
UISpecialFrames={}; SlashCmdList={}; DruidKitDB=nil
C_Timer = C_Timer or {}; C_Timer.After=function(t,f) PENDING=PENDING or {}; PENDING[#PENDING+1]=f end; C_Timer.NewTicker=function() return {Cancel=function() end} end
function InCombatLockdown() return false end
C_Map={GetBestMapForUnit=function() return 1453 end, GetMapInfo=function(id) return {name="Stormwind City",mapType=3} end, GetPlayerMapPosition=function() return {GetXY=function() return 0.5,0.5 end} end, GetMapChildrenInfo=function() return {} end, GetWorldPosFromMapPos=function() return nil end, SetUserWaypoint=function() end, ClearUserWaypoint=function() end}
function UnitIsDeadOrGhost() return false end function IsShiftKeyDown() return false end function ClearCursor() end function GetCursorInfo() end
function GetQuestID() return 0 end function GetTitleText() return "" end function GetQuestText() return "" end function GetObjectiveText() return "" end function GetProgressText() return "" end function GetRewardText() return "" end
function GetNumQuestChoices() return 0 end function GetQuestReward() end function IsQuestCompletable() return false end
function GetMoney() return 61362 end function CanMerchantRepair() return false end
MerchantFrame=MerchantFrame or nil
""")
order=["DruidKit_Guide.lua","DruidKit.lua","DruidKit_Helpers.lua","DruidKit_Trainers.lua","DruidKit_Steps.lua","DruidKit_Style.lua","DruidKit_Bags.lua","DruidKit_Bank.lua","DruidKit_Party.lua","DruidKit_DungeonData.lua","DruidKit_Dungeons.lua"]
errs=[]
for f in order:
    try: L.execute((Q/f).read_text(encoding='utf-8'))
    except Exception as e: errs.append(("load "+f, str(e)[:200]))
L.execute(r"""
ERR={}
local evs={"ADDON_LOADED","PLAYER_LOGIN","PLAYER_ENTERING_WORLD","BAG_UPDATE_DELAYED","MERCHANT_SHOW","MERCHANT_CLOSED","BANKFRAME_OPENED","QUEST_DETAIL","QUEST_PROGRESS","QUEST_COMPLETE","QUEST_TURNED_IN","PLAYER_LEVEL_UP","LOOT_OPENED","LOOT_CLOSED","PLAYER_REGEN_ENABLED","PLAYER_REGEN_DISABLED","GROUP_ROSTER_UPDATE","UNIT_AURA","TAXIMAP_OPENED","PLAYER_DEAD","ZONE_CHANGED_NEW_AREA","TRAINER_CLOSED","GOSSIP_SHOW"}
for _,e in ipairs(evs) do
  for i,f in ipairs(frames) do
    if f.on_OnEvent then local ok,er=pcall(f.on_OnEvent,f,e,"DruidKit") if not ok then ERR[#ERR+1]=e.." frame"..i..": "..tostring(er) end end
  end
  local n=0
  while PENDING and #PENDING>0 and n<200 do local fn=table.remove(PENDING,1); local ok,er=pcall(fn); if not ok then ERR[#ERR+1]="timer after "..e..": "..tostring(er) end n=n+1 end
end
for i,f in ipairs(frames) do if f.on_OnUpdate then local ok,er=pcall(f.on_OnUpdate,f,2.5) if not ok then ERR[#ERR+1]="OnUpdate frame"..i..": "..tostring(er) end end end
INCOMBAT=true; function InCombatLockdown() return true end
if DruidKit_ToggleSteps then local ok,er=pcall(DruidKit_ToggleSteps,false) if not ok then ERR[#ERR+1]="hide in combat: "..tostring(er) end; ok,er=pcall(DruidKit_ToggleSteps,true) if not ok then ERR[#ERR+1]="show in combat: "..tostring(er) end end
for i,f in ipairs(frames) do if f.on_OnUpdate then local ok,er=pcall(f.on_OnUpdate,f,2.5) if not ok then ERR[#ERR+1]="combat OnUpdate "..i..": "..tostring(er) end end end
for _,c in ipairs({"steps","bags","mount","pack","pack off","autosell","keymap","help","party test","party test","newspells","hud on","go"}) do
  local ok,er=pcall(SlashCmdList.DRUIDKIT,c) if not ok then ERR[#ERR+1]="/dk "..c..": "..tostring(er) end
end
""")
for e in errs: print("LOAD", e)
seen=set()
for e in L.globals().ERR.values():
    k=e[:160]
    if k not in seen: seen.add(k); print(k)
from expect import check, done
n=len(list(L.globals().ERR.values()))+len(errs)
check(n == 0, "no Lua errors across all modules, events, commands and combat", n)
done("smoke_test")
