"""Party view size: one column, scaled to fit the left third by height (text stays readable, floor 0.8 at normal);
/dk party size works relative to that; scale changes wait for the end of combat."""

from lupa.lua51 import LuaRuntime

from expect import check, done
from wowenv import mock, source

L = LuaRuntime(unpack_returned_tuples=True)
L.execute(
    mock("ui").replace(
        'if k=="CreateTexture" or k=="CreateFontString"',
        'if k=="CreateAnimationGroup" or k=="CreateAnimation" or k=="CreateMaskTexture" then return function() return mkobj() end end\n'
        '      if k=="CreateTexture" or k=="CreateFontString"',
    )
)
L.execute(r"""
DruidKitDB={}
COMBAT=false; function InCombatLockdown() return COMBAT end
function GetTime() return 100 end function RegisterUnitWatch() end function UnregisterUnitWatch() end
function RegisterStateDriver() end function UnregisterStateDriver() end
function UnitExists(u) return u=="player" end
function UnitIsVisible() return false end
C_ActionBar={GetActionInfo=function() end}
C_Spell={GetSpellInfo=function() end}
local cf=CreateFrame
function CreateFrame(kind, name)
  local f=cf(); if name then _G[name]=f end
  f.w, f.h, f.sc = 0, 0, 1
  function f:GetFrameLevel() return 1 end
  function f:SetSize(w, h) self.w, self.h = w, h end
  function f:GetWidth() return self.w end
  function f:GetHeight() return self.h end
  function f:SetScale(s) if COMBAT then error("scaled in combat") end self.sc=s end
  function f:GetScale() return self.sc end
  return f
end
UW, UH = 1365, 768
function UIParent:GetWidth() return UW end
function UIParent:GetHeight() return UH end
""")
L.execute(source("DruidKit/DruidKit_Party.lua"))
L.execute(r"""
for _,f in ipairs(frames) do if f.on_OnEvent then ev=f end end
ev.on_OnEvent(ev, "PLAYER_LOGIN")
P=_G.DruidKitParty
function sizeAt(arg) if arg then DruidKit_PartyCommand("size "..arg) end return P.sc end
""")
g = L.globals()
P = g.P

check(P.w < 1365 / 3 - 20, "one column of cards fits the left third at full size", P.w)
normal = g.sizeAt(None)
check(0.85 < normal < 0.87, "16:9: normal is limited by height (~0.86), not shrunk to fit two columns", normal)
check(P.h * normal <= 768 * 0.85 + 0.01, "16:9: normal fits the screen height", P.h * normal)
small, big = g.sizeAt("small"), g.sizeAt("big")
check(abs(small - 0.8 * normal) < 1e-6, "small is 0.8 times normal", small)
check(normal < big <= 768 / P.h + 1e-6, "big is bigger, never taller than the screen", big)
g.UH = 700
check(g.sizeAt("normal") == 0.8, "a short screen keeps normal at 0.8 (readable text)", g.sizeAt(None))
g.UH = 768

L.execute(r"""COMBAT=true; ev.on_OnEvent(ev, "PLAYER_REGEN_DISABLED"); DruidKit_PartyCommand("size small")""")
check(P.sc == 0.8, "no size change in combat", P.sc)
L.execute(r"""
COMBAT=false; DruidKitDB={partySize="small"}; frames={}; DruidKit_PartyCommand=nil
""")
L.execute(source("DruidKit/DruidKit_Party.lua"))
L.execute(r"""
for _,f in ipairs(frames) do if f.on_OnEvent then ev=f end end
COMBAT=true; ev.on_OnEvent(ev, "PLAYER_LOGIN"); P=_G.DruidKitParty; inCombat=P.sc
COMBAT=false; ev.on_OnEvent(ev, "PLAYER_REGEN_ENABLED"); after=P.sc
""")
check(g.inCombat == 1, "a reload in combat doesn't scale the secure view", g.inCombat)
check(abs(g.after - 0.8 * normal) < 1e-6, "it gets its size when combat ends", g.after)
done("r6_party_size_test")
