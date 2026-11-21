"""Window positions: one table of defaults used by every frame; the default layout keeps the middle of the screen clear
and frames apart; /dk resetpos clears saved spots and moves frames back (secure ones after combat)."""

import re

from expect import check, done
from wowenv import ROOT, runtime, source

L = runtime("ui")
L.execute(r"""
UISpecialFrames={}; SlashCmdList={}; DruidKitDB={}
C_Timer={After=function(d,f) f() end, NewTicker=function() end}
COMBAT=false; function InCombatLockdown() return COMBAT end
GetShapeshiftForm=function() return 0 end
function UnitIsDeadOrGhost() return false end
local cf=CreateFrame
function CreateFrame(kind, name) local f=cf(); if name then _G[name]=f end; return f end
-- a frame that remembers its anchor, can be dragged and knows its name
function MOVABLE(name, scale)
  local f={ name=name, scale=scale }
  function f:GetName() return self.name end
  function f:IsMovable() return true end
  function f:GetScale() return self.scale or 1 end
  function f:ClearAllPoints() self.pt=nil end
  function f:SetPoint(p, rel, rp, x, y)
    if COMBAT and self.secure then error("moved in combat") end
    self.pt={ p, rp, x, y }
  end
  function f:GetPoint() return self.pt[1], nil, self.pt[2], self.pt[3], self.pt[4] end
  _G[name]=f
  return f
end
""")
L.execute(source("DruidKit/DruidKit_Guide.lua"))
L.execute(source("DruidKit/DruidKit.lua"))
g = L.globals()
POS = g.DruidKitPos.DEFAULT

# 1. One table: no frame picks its own UIParent spot with numbers any more.
own = []
for f in sorted((ROOT / "DruidKit").glob("*.lua")):
    for n, line in enumerate(f.read_text(encoding="utf-8").splitlines(), 1):
        if re.search(r'SetPoint\("\w+",\s*UIParent,\s*"\w+",\s*-?\d', line):
            own.append(f"{f.name}:{n}")
check(not own, "no frame sets its own default spot on UIParent", own)
for name in [
    "arrow",
    "steps",
    "party",
    "rolls",
    "herb",
    "tracker",
    "hud",
    "rest",
    "warn",
    "guide",
    "lore",
    "bags",
    "bank",
    "loot",
    "dungeons",
    "share",
    "goto",
    "keys",
    "questxp",
]:
    check(POS[name] is not None and POS[name].frame, f"{name} has a default spot", name)

# 2. Layout. Sizes in screen units; the party view at its "normal" scale; the step window ~260 tall, 2 roll rows.
SIZE = {
    "arrow": (200, 120),
    "steps": (424, 260),
    "tracker": (280, 100),
    "herb": (260, 44),
    "rolls": (360, 180),
    "warn": (420, 40),
    "rest": (220, 40),
    "hud": (380, 34),
}
INCOMBAT = ["arrow", "steps", "tracker", "party", "rolls", "warn"]  # shown while you fight
OUTOFCOMBAT = ["herb", "rest", "hud"]


def rect(name, uw, uh):
    p = POS[name]
    w, h = SIZE.get(name, (0, 0))
    if name == "party":
        sc = min(1, (uw / 3 - 20) / 776)
        w, h = 776 * sc, 464 * sc
    ax = {"LEFT": 0, "CENTER": uw / 2, "RIGHT": uw}
    ay = {"TOP": uh, "CENTER": uh / 2, "BOTTOM": 0}

    def split(pt):
        v = "TOP" if pt.startswith("TOP") else "BOTTOM" if pt.startswith("BOTTOM") else "CENTER"
        hz = "LEFT" if pt.endswith("LEFT") else "RIGHT" if pt.endswith("RIGHT") else "CENTER"
        return v, hz

    rv, rh = split(p[2])
    fv, fh = split(p[1])
    x, y = ax[rh] + p[3], ay[rv] + p[4]
    left = x - {"LEFT": 0, "CENTER": w / 2, "RIGHT": w}[fh]
    bottom = y - {"BOTTOM": 0, "CENTER": h / 2, "TOP": h}[fv]
    return left, bottom, left + w, bottom + h


def hit(a, b):
    return a[0] < b[2] and b[0] < a[2] and a[1] < b[3] and b[1] < a[3]


for uw, label in [(1365, "16:9"), (1792, "21:9")]:
    uh = 768
    middle = (uw / 3, uh - 600, 2 * uw / 3, uh - 340)  # the character and the mob in front of it
    on = [n for n in INCOMBAT if hit(rect(n, uw, uh), middle)]
    check(not on, f"{label}: nothing shown in combat covers the middle of the screen", on)
    shown = INCOMBAT + OUTOFCOMBAT
    pairs = [(a, b) for i, a in enumerate(shown) for b in shown[i + 1 :] if hit(rect(a, uw, uh), rect(b, uw, uh))]
    check(not pairs, f"{label}: no two always-there frames overlap by default", pairs)
    check(rect("arrow", uw, uh)[0] < uw / 2 < rect("arrow", uw, uh)[2], f"{label}: the arrow is top-centre")
    check(rect("steps", uw, uh)[0] > 2 * uw / 3, f"{label}: the step window is on the right")
    check(rect("party", uw, uh)[2] < uw / 3, f"{label}: the party view is on the left")

# 3. Saved spots: new, and the ones saved before this table.
L.execute(r"""
R={}
DruidKitDB={ stepsPos={ -50, -300 }, partyPos3={ "TOPLEFT", "TOPLEFT", 40, -200 },
  panels={ hud={ "CENTER", "CENTER", 5, 5 } }, guideFrame={ point="LEFT", relPoint="LEFT", x=1, y=2, w=600, h=500 } }
S=MOVABLE("DruidKitSteps"); P=MOVABLE("DruidKitParty", 0.5); P.secure=true; H=MOVABLE("DruidKit_hud"); G=MOVABLE("DruidKitGuideFrame")
A=MOVABLE("DruidKitArrow")
DruidKitPos.place(S, "steps"); DruidKitPos.place(P, "party"); DruidKitPos.place(H); DruidKitPos.place(G); DruidKitPos.place(A)
R.steps=table.concat(S.pt, " "); R.party=table.concat(P.pt, " "); R.hud=table.concat(H.pt, " "); R.guide=table.concat(G.pt, " ")
R.arrow=table.concat(A.pt, " ")
A.pt={ "BOTTOMLEFT", "BOTTOMLEFT", 300, 400 }; DruidKitPos.save(A); DruidKitPos.place(A, "arrow"); R.dragged=table.concat(A.pt, " ")
""")
R = g.R
check(R.steps == "TOPRIGHT TOPRIGHT -50 -300", "a step window dragged before keeps its spot", R.steps)
check(R.party == "TOPLEFT TOPLEFT 40 -200", "a party view dragged before keeps its spot", R.party)
check(R.hud == "CENTER CENTER 5 5", "a helper panel dragged before keeps its spot", R.hud)
check(R.guide == "LEFT LEFT 1 2", "a guide dragged before keeps its spot", R.guide)
check(R.arrow == "TOP TOP 0 -215", "the arrow gets its default", R.arrow)
check(R.dragged == "BOTTOMLEFT BOTTOMLEFT 300 400", "a drag saves the whole anchor, not just x and y", R.dragged)

# 4. /dk resetpos in combat: everything forgotten, the secure party view moves after combat.
L.execute(r"""
COMBAT=true; printed={}
SlashCmdList.DRUIDKIT("resetpos")
R.out=table.concat(printed, " | ")
R.cleared=tostring(DruidKitDB.stepsPos==nil and DruidKitDB.partyPos3==nil and (DruidKitDB.panels or {}).hud==nil
  and DruidKitDB.guideFrame.point==nil and DruidKitDB.guideFrame.w==600 and (DruidKitDB.pos or {}).arrow==nil)
R.steps=table.concat(S.pt, " "); R.partyIn=table.concat(P.pt, " "); R.arrow=table.concat(A.pt, " ")
COMBAT=false
for _, f in ipairs(frames) do if f.on_OnEvent then f.on_OnEvent(f, "PLAYER_REGEN_ENABLED") end end
R.partyAfter=table.concat(P.pt, " ")
DruidKitDB.pos={ steps={ "TOP", "TOP", 1, 1 }, arrow={ "TOP", "TOP", 2, 2 } }
printed={}; SlashCmdList.DRUIDKIT("resetpos steps")
R.one=table.concat(printed, " | "); R.keep=tostring(DruidKitDB.pos.arrow ~= nil and DruidKitDB.pos.steps == nil)
printed={}; SlashCmdList.DRUIDKIT("resetpos nope"); R.bad=table.concat(printed, " | ")
""")
check(R.cleared == "true", "every saved spot is forgotten (the guide keeps its size)", R.cleared)
check(
    R.steps == "BOTTOMRIGHT BOTTOMRIGHT -10 140" and R.arrow == "TOP TOP 0 -215",
    "frames go back now",
    (R.steps, R.arrow),
)
check(R.partyIn == "TOPLEFT TOPLEFT 40 -200", "the secure party view is not moved in combat", R.partyIn)
check("after combat: party" in R.out and "steps" in R.out and "arrow" in R.out, "it lists what it reset", R.out)
check(
    R.partyAfter == "TOPLEFT TOPLEFT 20 -280",
    "the party view moves after combat (default in screen units)",
    R.partyAfter,
)
check(R.keep == "true" and "steps" in R.one and "arrow" not in R.one, "/dk resetpos steps resets only that", R.one)
check("no window called 'nope'" in R.bad and "steps" in R.bad, "an unknown name lists the names", R.bad)
done("r5_ui_pos_test")
