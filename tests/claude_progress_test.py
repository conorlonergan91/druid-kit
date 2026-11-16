"""ClaudeProgress: bank (old and modern events), recipes (classic and C_TradeSkillUI), and profession tracker lines."""

from lupa.lua51 import LuaRuntime

from wowenv import source


def runtime(modern):
    L = LuaRuntime(unpack_returned_tuples=True)
    L.execute("""
SlashCmdList={} timers={}
C_Timer={After=function(t,f) table.insert(timers,f) end, NewTicker=function() end}
function CreateFrame() local f={} function f:RegisterEvent() end function f:SetScript(k,fn) f[k]=fn end frames=frames or {} table.insert(frames,f) return f end
function UnitName() return "Cu" end function GetRealmName() return "R5" end
function date() return "x" end function time() return 1 end
BANK_CONTAINER=-1 NUM_BAG_SLOTS=4 NUM_BANKBAGSLOTS=7
bags={[0]={{"|Hitem:765|h[Silverleaf]|h",7,765}},[-1]={{"|Hitem:2589|h[Linen Cloth]|h",20,2589}},[6]={{"|Hitem:3371|h[Empty Vial]|h",17,3371}}}
C_Container={GetContainerNumSlots=function(b) return bags[b] and #bags[b] or 0 end,
 GetContainerItemInfo=function(b,s) local e=bags[b][s]; return {hyperlink=e[1],stackCount=e[2],itemID=e[3]} end}
function GetItemInfo(l) return (type(l)=="string" and l:match("%[(.-)%]")) or "X",nil,1,nil,nil,"Trade Goods","Herb" end
function run(ev, a1) for _,f in ipairs(frames) do if f.OnEvent then f.OnEvent(f, ev, a1) end end
  local i=1; while timers[i] do timers[i](); i=i+1 end; timers={} end
""")
    if modern:
        L.execute("""
Enum={BagIndex={Bank=-1,CharacterBankTab_1=6},PlayerInteractionType={Banker=8}}
C_Item={GetItemNameByID=function(id) return ({[2447]="Peacebloom",[3371]="Empty Vial"})[id] end, GetItemCount=function() return 3 end}
C_TradeSkillUI={GetBaseProfessionInfo=function() return {professionName="",parentProfessionName="",professionID=171,skillLevel=59,maxSkillLevel=75} end,
 GetChildProfessionInfo=function() return {professionName="",professionID=2937,skillLevel=59,maxSkillLevel=75} end,
 GetAllRecipeIDs=function() return {1} end,
 GetRecipeInfo=function() return {learned=true,name="Minor Mana Potion",relativeDifficulty=0,numAvailable=2} end,
 GetRecipeSchematic=function() return {reagentSlotSchematics={{quantityRequired=1,reagents={{itemID=2447}}},{quantityRequired=1,reagents={{itemID=3371}}}}} end}""")
    else:
        L.execute("""
function GetTradeSkillLine() return "Alchemy",47,75 end
function GetNumTradeSkills() return 2 end
function GetTradeSkillInfo(i) if i==1 then return "Elixir of Minor Defense","optimal",5 else return "Herbs","header" end end
function GetTradeSkillNumReagents() return 2 end
function GetTradeSkillReagentInfo(i,j) return ({"Silverleaf","Peacebloom"})[j],nil,1,7 end""")
    L.execute(source("ClaudeProgress/ClaudeProgress.lua"))
    return L


ok = True
L = runtime(False)
L.execute('run("BANKFRAME_OPENED"); run("TRADE_SKILL_SHOW")')
ok &= L.eval('ClaudeProgressDB.bank["Cu-R5"].items["Linen Cloth"].count') == 20
ok &= L.eval('ClaudeProgressDB.recipes["Cu-R5"]["Alchemy"].list[1].colour') == "orange"
L = runtime(True)
L.execute('run("PLAYER_INTERACTION_MANAGER_FRAME_SHOW", 8); run("TRADE_SKILL_SHOW")')
ok &= L.eval('ClaudeProgressDB.bank["Cu-R5"].items["Empty Vial"].count') == 17
ok &= L.eval('ClaudeProgressDB.recipes["Cu-R5"]["Alchemy"].list[1].reagents[1].name') == "Peacebloom"
ok &= L.eval('ClaudeProgressDB.recipes["Cu-R5"]["Alchemy"].rank') == 59
# tracker lines
L = LuaRuntime(unpack_returned_tuples=True)
src = source("DruidKit/DruidKit_Helpers.lua")
code = (
    'local DRUID, LEAF, RED, GREY = "","","",""\n'
    + src[src.index("-- Professions: say when") : src.index("DruidKit_ProfessionLines = professionLines")]
    + "return professionLines"
)
L.execute("""skills={{"Alchemy",false,0,59,0,0,75},{"Fishing",false,0,29,0,0,75},{"Cooking",false,0,130,0,0,150}}
function GetNumSkillLines() return #skills end
function GetSkillLineInfo(i) return (table.unpack or unpack)(skills[i],1,7) end""")
lines = list(L.execute(code)().values())
ok &= len(lines) == 2 and "Alchemy" in lines[0] and "Cooking" in lines[1]
print("cp_test", "OK" if ok else "FAIL")
