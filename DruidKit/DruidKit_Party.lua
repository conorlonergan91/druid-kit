-- Druid Kit: party healer view (v3, big cards).
-- A column of large cards (left side of the screen, movable). Each card has the person's
-- portrait, a big health bar, and a row of YOUR healing buttons taken from your action bars:
-- same icons, same cooldown sweep, and one click casts that spell on that person.
--   Card click: target · Right-click: Rejuvenation · Shift Regrowth · Ctrl Healing Touch · Alt Cure Poison
-- Accessibility: every alert is a word or letter, never colour alone.
--   Poison / curse: big "P" / "C" button on the portrait pulses: click it to cure.
--   Missing Mark of the Wild: "!" button on the portrait.  Aggro on a non-tank: "AGGRO" tag.
--   Low health: "LOW 42%". Critical (under 30%): "!! 25%" and the whole card pulses white. Dead: "DEAD".
--   /dk party test · /dk party on|off · /dk party size small|normal|big · /dk unlock to move

local ORANGE, LEAF = { 1, 0.49, 0.04 }, { 0.5, 0.83, 0.36 }
local PORTRAIT, BTN, BTN_GAP, MAX_BTNS = 84, 34, 3, 7
local CARD_W = 12 + PORTRAIT + 8 + 12 + MAX_BTNS * BTN + (MAX_BTNS - 1) * BTN_GAP + 12
local CARD_H, PET_H, GAP = 116, 20, 8
local SIZES = { small = 0.8, normal = 1.0, big = 1.2 }
local COLS, ROWS, HEADER_H = 2, 3, 26        -- you top-left, then your party; fits on screen
local BARK, GOLD = { 0.45, 0.32, 0.16 }, { 0.85, 0.68, 0.3 }
local RESTO_BG = "Interface\\TalentFrame\\DruidRestoration-TopLeft"
local UNITS = { "player", "party1", "party2", "party3", "party4" }
local PETS = { "pet", "partypet1", "partypet2", "partypet3", "partypet4" }
local MY_HOTS = { "Rejuvenation", "Regrowth" }
-- Spells worth a button on a party card, in this order (only ones on your bars are used).
local CARD_SPELLS = { "Rejuvenation", "Regrowth", "Healing Touch", "Swiftmend", "Wild Growth", "Lifebloom",
                      "Nourish", "Abolish Poison", "Cure Poison", "Remove Curse", "Rebirth", "Innervate" }
local CRITICAL, LOW = 0.30, 0.50
local MASK = "Interface\\CharacterFrame\\TempPortraitAlphaMask"

local function say(msg) print("|cff7fd35bDruid Kit:|r " .. msg) end
local seenErr = {}
local function logErr(where, err)
  err = tostring(err)
  if seenErr[where .. err] then return end
  seenErr[where .. err] = true
  DruidKitDB = DruidKitDB or {}
  DruidKitDB.partyLog = DruidKitDB.partyLog or {}
  local log = DruidKitDB.partyLog
  table.insert(log, (date and date("%H:%M:%S") or "") .. " " .. where .. ": " .. err)
  while #log > 25 do table.remove(log, 1) end
end
local function plain(v) if v == nil then return nil end if issecretvalue and issecretvalue(v) then return nil end return v end
local function try(fn, ...) if not fn then return end local ok, a, b, c, d = pcall(fn, ...) if ok then return a, b, c, d end end

-- Fonts: big, outlined, easy to read over anything.
local FONT = "Fonts\\FRIZQT__.TTF"
local function text(parent, size, layer)
  local fs = parent:CreateFontString(nil, layer or "OVERLAY")
  fs:SetFont(FONT, size, "OUTLINE")
  fs:SetShadowOffset(1, -1); fs:SetShadowColor(0, 0, 0, 1)
  fs:SetWordWrap(false)
  return fs
end

local container, cards, pets, testing = nil, {}, {}, false
local slotsDirty = true
local DB

local function healthFrac(unit)
  local c, m = plain(try(UnitHealth, unit)), plain(try(UnitHealthMax, unit))
  if c and m and m > 0 then return c / m end
  if UnitHealthPercent then
    local p = plain(try(UnitHealthPercent, unit))
    if p then return p > 1 and p / 100 or p end
  end
end

local function knownSpell(name)
  local id
  if C_Spell and C_Spell.GetSpellInfo then
    local info = try(C_Spell.GetSpellInfo, name)
    id = type(info) == "table" and plain(info.spellID) or nil
  end
  if not id and GetSpellInfo then
    local ok, _, _, _, _, _, _, gid = pcall(GetSpellInfo, name)
    if ok then id = plain(gid) end
  end
  if not id then return false end
  if C_SpellBook and C_SpellBook.IsSpellKnown then return try(C_SpellBook.IsSpellKnown, id) and true or false end
  if IsPlayerSpell then return try(IsPlayerSpell, id) and true or false end
  if IsSpellKnown then return try(IsSpellKnown, id) and true or false end
  return true
end

local function auraByName(unit, name, filter)
  if C_UnitAuras and C_UnitAuras.GetAuraDataBySpellName then
    return try(C_UnitAuras.GetAuraDataBySpellName, unit, name, filter)
  end
end

-- Action-bar helpers (read only: we never change your bars) -------------------------
local function actionTexture(slot)
  if C_ActionBar and C_ActionBar.GetActionTexture then return try(C_ActionBar.GetActionTexture, slot) end
  return try(GetActionTexture, slot)
end
local function actionSpellName(slot)
  local kind, id
  if C_ActionBar and C_ActionBar.GetActionInfo then kind, id = try(C_ActionBar.GetActionInfo, slot)
  else kind, id = try(GetActionInfo, slot) end
  kind, id = plain(kind), plain(id)
  if kind ~= "spell" or not id then return end
  if C_Spell and C_Spell.GetSpellName then return plain(try(C_Spell.GetSpellName, id)) end
  return plain(try(GetSpellInfo, id))
end
-- Find the first action slot holding each card spell (main bar first, then the others).
local function findCardSlots()
  local found, out = {}, {}
  for slot = 1, 120 do
    local n = actionSpellName(slot)
    if n and not found[n] then found[n] = slot end
  end
  for _, n in ipairs(CARD_SPELLS) do
    if found[n] and #out < MAX_BTNS then table.insert(out, { slot = found[n], name = n }) end
  end
  return out
end

-- Cooldown sweep that copes with hidden ("secret") values in combat.
local function setCooldown(cd, slot)
  if C_ActionBar and C_ActionBar.GetActionCooldownDuration and cd.SetCooldownFromDurationObject then
    local d = try(C_ActionBar.GetActionCooldownDuration, slot)
    if d and pcall(cd.SetCooldownFromDurationObject, cd, d) then return end
  end
  local s, dur
  if C_ActionBar and C_ActionBar.GetActionCooldown then
    local info = try(C_ActionBar.GetActionCooldown, slot)
    if type(info) == "table" then s, dur = info.startTime, info.duration end
  else
    s, dur = try(GetActionCooldown, slot)
  end
  s, dur = plain(s), plain(dur)
  if s and dur and dur > 1.5 then pcall(cd.SetCooldown, cd, s, dur) elseif s then pcall(cd.Clear, cd) end
end

-- Pieces ---------------------------------------------------------------------------------
local function pulseAnim(f, from, to)
  local g = f:CreateAnimationGroup(); g:SetLooping("BOUNCE")
  local a = g:CreateAnimation("Alpha"); a:SetFromAlpha(from); a:SetToAlpha(to); a:SetDuration(0.45); a:SetSmoothing("IN_OUT")
  return g
end

local function makeHot(parent, size)
  local f = CreateFrame("Frame", nil, parent)
  f:SetSize(size, size)
  f.edge = f:CreateTexture(nil, "BACKGROUND"); f.edge:SetPoint("TOPLEFT", -1, 1); f.edge:SetPoint("BOTTOMRIGHT", 1, -1); f.edge:SetColorTexture(0, 0, 0, 1)
  f.tex = f:CreateTexture(nil, "ARTWORK"); f.tex:SetAllPoints(); f.tex:SetTexCoord(0.08, 0.92, 0.08, 0.92)
  f.txt = text(f, 13); f.txt:SetPoint("BOTTOMRIGHT", 2, -1)
  f:Hide()
  return f
end

-- Big lettered fix button on the portrait (P / C / !). Secure, so it fades instead of hiding in combat.
local function makeFix(parent, spell, icon, letter, tip)
  local f = CreateFrame("Button", nil, parent, "SecureActionButtonTemplate")
  f:SetSize(30, 30)
  f:RegisterForClicks("AnyUp", "AnyDown")
  f:SetAttribute("type", "spell"); f:SetAttribute("spell", spell)
  f.edge = f:CreateTexture(nil, "BACKGROUND"); f.edge:SetPoint("TOPLEFT", -2, 2); f.edge:SetPoint("BOTTOMRIGHT", 2, -2); f.edge:SetColorTexture(1, 1, 1, 1)
  f.tex = f:CreateTexture(nil, "ARTWORK"); f.tex:SetAllPoints(); f.tex:SetTexCoord(0.08, 0.92, 0.08, 0.92); f.tex:SetTexture(icon)
  f.shade = f:CreateTexture(nil, "ARTWORK", nil, 1); f.shade:SetAllPoints(); f.shade:SetColorTexture(0, 0, 0, 0.35)
  f.badge = text(f, 20); f.badge:SetPoint("CENTER", 0, 0); f.badge:SetText(letter)
  local hl = f:CreateTexture(nil, "HIGHLIGHT"); hl:SetAllPoints(); hl:SetColorTexture(1, 1, 1, 0.25)
  f.pulse = pulseAnim(f, 1, 0.45)
  f:SetScript("OnEnter", function(s)
    if s:GetAlpha() < 0.1 then return end
    GameTooltip:SetOwner(s, "ANCHOR_TOP"); GameTooltip:AddLine("Click: " .. tip, 1, 1, 1); GameTooltip:Show()
  end)
  f:SetScript("OnLeave", function() GameTooltip:Hide() end)
  f:SetAlpha(0); f:EnableMouse(false); f.mouseOn = false
  return f
end
-- A hidden fix button must not take clicks. Secure frames can't change that in combat: done after combat.
-- P, C and R are needed mid-fight, so all of them take clicks from the start of combat until it ends.
local mouseLater = {}
local combatFixes = {}
local function setMouse(f, on)
  if f.mouseOn == on and mouseLater[f] == nil then return end
  if InCombatLockdown() then mouseLater[f] = on; return end
  mouseLater[f] = nil
  f:EnableMouse(on); f.mouseOn = on
end
local function applyMouseLater()
  for f, on in pairs(mouseLater) do mouseLater[f] = nil; f:EnableMouse(on); f.mouseOn = on end
end
local function combatReady()
  if InCombatLockdown() then return end
  for f in pairs(combatFixes) do mouseLater[f] = nil; f:EnableMouse(true); f.mouseOn = true end
end
local function afterCombat()
  applyMouseLater()
  for f in pairs(combatFixes) do setMouse(f, f.isOn == true) end
end
local function showFix(f, on, pulse)
  f.isOn = on and true or false
  setMouse(f, f.isOn or (combatFixes[f] ~= nil and InCombatLockdown()))
  if on then
    if pulse then if not f.pulse:IsPlaying() then f.pulse:Play() end
    elseif f.pulse:IsPlaying() then f.pulse:Stop() end
    if not f.pulse:IsPlaying() then f:SetAlpha(1) end
  else
    if f.pulse:IsPlaying() then f.pulse:Stop() end
    f:SetAlpha(0)
  end
end

-- One of your spells, cast on this card's person. Reads the icon and cooldown from your action slot.
local function makeSpellButton(card, i)
  local f = CreateFrame("Button", nil, card, "SecureActionButtonTemplate")
  f:SetSize(BTN, BTN)
  f:RegisterForClicks("AnyUp", "AnyDown")
  f:SetAttribute("type", "action")
  f.edge = f:CreateTexture(nil, "BACKGROUND"); f.edge:SetPoint("TOPLEFT", -1, 1); f.edge:SetPoint("BOTTOMRIGHT", 1, -1); f.edge:SetColorTexture(0, 0, 0, 1)
  f.tex = f:CreateTexture(nil, "ARTWORK"); f.tex:SetAllPoints(); f.tex:SetTexCoord(0.08, 0.92, 0.08, 0.92)
  f.cd = CreateFrame("Cooldown", nil, f, "CooldownFrameTemplate"); f.cd:SetAllPoints()
  if f.cd.SetHideCountdownNumbers then f.cd:SetHideCountdownNumbers(false) end
  f.badge = text(f, 16); f.badge:SetPoint("CENTER")
  local hl = f:CreateTexture(nil, "HIGHLIGHT"); hl:SetAllPoints(); hl:SetColorTexture(1, 1, 1, 0.25)
  local pushed = f:CreateTexture(nil, "OVERLAY"); pushed:SetAllPoints(); pushed:SetColorTexture(1, 1, 1, 0.35); f:SetPushedTexture(pushed)
  f.pulse = pulseAnim(f, 1, 0.45)
  f:SetScript("OnEnter", function(s)
    if not s.slot then return end
    GameTooltip:SetOwner(s, "ANCHOR_TOP")
    pcall(GameTooltip.SetAction, GameTooltip, s.slot)
    local who = plain(try(UnitName, card.unit)) or "them"
    GameTooltip:AddLine("Click: cast on " .. tostring(who), 0.5, 0.83, 0.36)
    GameTooltip:Show()
  end)
  f:SetScript("OnLeave", function() GameTooltip:Hide() end)
  f:SetAlpha(0)
  return f
end

local BAR_TEX = "Interface\\Buttons\\WHITE8x8"

local function makeCard(i, unit)
  local b = CreateFrame("Button", "DruidKitPartyCard" .. i, container, "SecureUnitButtonTemplate,BackdropTemplate")
  b:SetSize(CARD_W, CARD_H)
  local col, row = (i - 1) % COLS, math.floor((i - 1) / COLS)
  b:SetPoint("TOPLEFT", container, "TOPLEFT", col * (CARD_W + GAP), -HEADER_H - row * (CARD_H + PET_H + GAP + 2))
  b:RegisterForClicks("AnyUp")
  b:SetAttribute("unit", unit)
  b:SetAttribute("type1", "target")
  b:SetAttribute("type2", "spell");        b:SetAttribute("spell2", "Rejuvenation")
  b:SetAttribute("shift-type1", "spell");  b:SetAttribute("shift-spell1", "Regrowth")
  b:SetAttribute("ctrl-type1", "spell");   b:SetAttribute("ctrl-spell1", "Healing Touch")
  b:SetAttribute("alt-type1", "spell");    b:SetAttribute("alt-spell1", "Cure Poison")
  b.unit = unit
  -- Druid look: Restoration-tree artwork under a deep forest-green tint, bark-and-gold border.
  if b.SetBackdrop then
    b:SetBackdrop({ bgFile = BAR_TEX, edgeFile = "Interface\\Tooltips\\UI-Tooltip-Border", edgeSize = 14,
                    insets = { left = 3, right = 3, top = 3, bottom = 3 } })
    b:SetBackdropColor(0.02, 0.06, 0.03, 0.95)
    b:SetBackdropBorderColor(GOLD[1], GOLD[2], GOLD[3], 1)
  end
  b.art = b:CreateTexture(nil, "BACKGROUND", nil, 1); b.art:SetPoint("TOPLEFT", 4, -4); b.art:SetPoint("BOTTOMRIGHT", -4, 4)
  b.art:SetTexture(RESTO_BG); b.art:SetTexCoord(0.1, 0.9, 0.25, 0.6); b.art:SetAlpha(0.45)
  b.shade = b:CreateTexture(nil, "BACKGROUND", nil, 2); b.shade:SetAllPoints(b.art); b.shade:SetTexture(BAR_TEX)
  if b.shade.SetGradient and CreateColor then
    pcall(b.shade.SetGradient, b.shade, "HORIZONTAL", CreateColor(0.02, 0.08, 0.03, 0.55), CreateColor(0.01, 0.04, 0.02, 0.85))
  else b.shade:SetColorTexture(0.02, 0.07, 0.03, 0.7) end
  -- class-colour stripe down the left edge (who they are at a glance)
  b.stripe = b:CreateTexture(nil, "ARTWORK", nil, -1); b.stripe:SetPoint("TOPLEFT", 4, -4); b.stripe:SetPoint("BOTTOMLEFT", 4, 4); b.stripe:SetWidth(4)
  b.stripe:SetColorTexture(1, 1, 1, 1)
  -- critical pulse (white, behind) and target edge with a word
  b.glow = b:CreateTexture(nil, "BACKGROUND", nil, -1)
  b.glow:SetPoint("TOPLEFT", -5, 5); b.glow:SetPoint("BOTTOMRIGHT", 5, -5); b.glow:SetColorTexture(1, 1, 1, 1); b.glow:SetAlpha(0)
  b.pulse = b.glow:CreateAnimationGroup(); b.pulse:SetLooping("BOUNCE")
  local a = b.pulse:CreateAnimation("Alpha"); a:SetFromAlpha(0.15); a:SetToAlpha(0.8); a:SetDuration(0.55); a:SetSmoothing("IN_OUT")
  b.selEdge = CreateFrame("Frame", nil, b, "BackdropTemplate"); b.selEdge:SetPoint("TOPLEFT", -3, 3); b.selEdge:SetPoint("BOTTOMRIGHT", 3, -3)
  if b.selEdge.SetBackdrop then b.selEdge:SetBackdrop({ edgeFile = BAR_TEX, edgeSize = 3 }); b.selEdge:SetBackdropBorderColor(ORANGE[1], ORANGE[2], ORANGE[3], 1) end
  b.selEdge.t = text(b.selEdge, 13); b.selEdge.t:SetPoint("BOTTOMRIGHT", -8, 4); b.selEdge.t:SetText("TARGET"); b.selEdge.t:SetTextColor(ORANGE[1], ORANGE[2], ORANGE[3])
  b.selEdge:Hide()

  -- portrait: gold ring, dark ring, round face (the game draws faces round already)
  b.ringGold = b:CreateTexture(nil, "ARTWORK", nil, 0); b.ringGold:SetSize(PORTRAIT + 8, PORTRAIT + 8); b.ringGold:SetPoint("LEFT", 12, 0)
  b.ringGold:SetTexture(MASK); b.ringGold:SetVertexColor(GOLD[1], GOLD[2], GOLD[3], 1)
  b.ring = b:CreateTexture(nil, "ARTWORK", nil, 1); b.ring:SetSize(PORTRAIT + 2, PORTRAIT + 2); b.ring:SetPoint("CENTER", b.ringGold)
  b.ring:SetTexture(MASK); b.ring:SetVertexColor(0.02, 0.02, 0.02, 1)
  b.portrait = b:CreateTexture(nil, "ARTWORK", nil, 2); b.portrait:SetSize(PORTRAIT, PORTRAIT); b.portrait:SetPoint("CENTER", b.ringGold)
  b.level = CreateFrame("Frame", nil, b, "BackdropTemplate"); b.level:SetSize(34, 22); b.level:SetPoint("BOTTOM", b.ringGold, "BOTTOM", 0, -4)
  if b.level.SetBackdrop then b.level:SetBackdrop({ bgFile = BAR_TEX, edgeFile = BAR_TEX, edgeSize = 1 }); b.level:SetBackdropColor(0, 0, 0, 0.9); b.level:SetBackdropBorderColor(0.85, 0.68, 0.3, 1) end
  b.level:SetFrameLevel(b:GetFrameLevel() + 6)
  b.level.t = text(b.level, 13); b.level.t:SetPoint("CENTER", 0, 0)
  b.big = text(b, 26); b.big:SetPoint("CENTER", b.portrait, "CENTER", 0, 4)   -- DEAD / !! over the face

  local x0 = 12 + PORTRAIT + 8 + 12
  -- name (class colour) and health % on the same line
  b.name = text(b, 18); b.name:SetPoint("TOPLEFT", x0, -8); b.name:SetPoint("RIGHT", -96, 0); b.name:SetJustifyH("LEFT")
  b.state = text(b, 18); b.state:SetPoint("TOPRIGHT", -10, -8); b.state:SetJustifyH("RIGHT")
  -- health bar with the real numbers on it
  b.hp = CreateFrame("StatusBar", nil, b, "BackdropTemplate")
  b.hp:SetPoint("TOPLEFT", x0, -32); b.hp:SetPoint("RIGHT", -10, 0); b.hp:SetHeight(26)
  b.hp:SetStatusBarTexture("Interface\\TargetingFrame\\UI-StatusBar"); b.hp:SetStatusBarColor(LEAF[1], LEAF[2], LEAF[3])
  b.hp.bg = b.hp:CreateTexture(nil, "BACKGROUND"); b.hp.bg:SetAllPoints(); b.hp.bg:SetColorTexture(0.18, 0.07, 0.04, 0.95)   -- missing health = dark bark-red
  if b.hp.SetBackdrop then b.hp:SetBackdrop({ edgeFile = BAR_TEX, edgeSize = 1 }); b.hp:SetBackdropBorderColor(0, 0, 0, 1) end
  b.hp.shine = b.hp:CreateTexture(nil, "OVERLAY"); b.hp.shine:SetPoint("TOPLEFT"); b.hp.shine:SetPoint("TOPRIGHT"); b.hp.shine:SetHeight(9); b.hp.shine:SetColorTexture(1, 1, 1, 0.12)
  b.hpText = text(b.hp, 14); b.hpText:SetPoint("LEFT", 8, 0); b.hpText:SetJustifyH("LEFT")
  b.hots = {}
  for h = 1, #MY_HOTS do
    local ic = makeHot(b.hp, 22)
    ic:SetPoint("RIGHT", b.hp, "RIGHT", -2 - (h - 1) * 25, 0); ic:SetFrameLevel(b.hp:GetFrameLevel() + 2)
    b.hots[h] = ic
  end
  b.aggro = CreateFrame("Frame", nil, b, "BackdropTemplate"); b.aggro:SetSize(70, 20); b.aggro:SetPoint("TOP", b, "TOP", 40, 10)
  if b.aggro.SetBackdrop then b.aggro:SetBackdrop({ bgFile = BAR_TEX, edgeFile = BAR_TEX, edgeSize = 2 }); b.aggro:SetBackdropColor(0, 0, 0, 0.95); b.aggro:SetBackdropBorderColor(1, 1, 1, 1) end
  b.aggro:SetFrameLevel(b:GetFrameLevel() + 9)
  b.aggro.t = text(b.aggro, 13); b.aggro.t:SetPoint("CENTER"); b.aggro.t:SetText("AGGRO")
  b.aggro:Hide()
  -- mana bar with numbers
  b.mp = CreateFrame("StatusBar", nil, b)
  b.mp:SetPoint("TOPLEFT", b.hp, "BOTTOMLEFT", 0, -3); b.mp:SetPoint("TOPRIGHT", b.hp, "BOTTOMRIGHT", 0, -3); b.mp:SetHeight(14)
  b.mp:SetStatusBarTexture("Interface\\TargetingFrame\\UI-StatusBar"); b.mp:SetStatusBarColor(0.2, 0.5, 1)
  b.mp.bg = b.mp:CreateTexture(nil, "BACKGROUND"); b.mp.bg:SetAllPoints(); b.mp.bg:SetColorTexture(0.05, 0.07, 0.16, 0.95)
  b.mpText = text(b.mp, 13); b.mpText:SetPoint("RIGHT", -4, 0)
  -- your spells, bottom row
  b.btns = {}
  for n = 1, MAX_BTNS do
    local s = makeSpellButton(b, n)
    s:SetPoint("BOTTOMLEFT", x0 + (n - 1) * (BTN + BTN_GAP), 8)
    s:SetFrameLevel(b:GetFrameLevel() + 5)
    b.btns[n] = s
  end
  -- fixes on the portrait: ! top-left, P bottom-left, C bottom-right
  b.motw = makeFix(b, "Mark of the Wild", "Interface\\Icons\\Spell_Nature_Regeneration", "!", "Mark of the Wild")
  -- Secure buttons may only anchor to frames, not textures: place them on the card at the portrait's corners.
  local pTop = (CARD_H - PORTRAIT) / 2
  b.motw:SetPoint("TOPLEFT", b, "TOPLEFT", 16 - 6, -(pTop - 6))
  b.cureP = makeFix(b, "Cure Poison", "Interface\\Icons\\Spell_Nature_NullifyPoison", "P", "Cure Poison")
  b.cureP:SetPoint("BOTTOMLEFT", b, "BOTTOMLEFT", 16 - 6, pTop - 6)
  b.cureC = makeFix(b, "Remove Curse", "Interface\\Icons\\Spell_Holy_RemoveCurse", "C", "Remove Curse")
  b.cureC:SetPoint("BOTTOMRIGHT", b, "BOTTOMLEFT", 16 + PORTRAIT + 6, pTop - 6)
  -- T (top-right): Thorns missing on whoever is tanking or being hit
  b.thorns = makeFix(b, "Thorns", "Interface\\Icons\\Spell_Nature_Thorns", "T", "Thorns")
  b.thorns:SetPoint("TOPRIGHT", b, "TOPLEFT", 16 + PORTRAIT + 6, -(pTop - 6))
  -- R (middle of the face): bring them back. Out of combat Revive, in combat Rebirth.
  b.res = makeFix(b, "Revive", "Interface\\Icons\\Spell_Nature_Reincarnation", "R", "Revive (Rebirth in combat)")
  b.res:SetSize(44, 44)
  b.res:SetPoint("CENTER", b, "LEFT", 16 + PORTRAIT / 2, 0)
  b.res:SetAttribute("type", "macro")
  for _, f in ipairs({ b.motw, b.cureP, b.cureC, b.thorns, b.res }) do f:SetAttribute("unit", unit); f:SetFrameLevel(b:GetFrameLevel() + 8) end
  for _, f in ipairs({ b.cureP, b.cureC, b.res }) do combatFixes[f] = true end
  b.res:SetAttribute("macrotext", ("/cast [@%s,combat] Rebirth; [@%s] Revive"):format(unit, unit))

  b:SetScript("OnEnter", function(s)
    GameTooltip_SetDefaultAnchor(GameTooltip, s)
    if UnitExists(s.unit) then pcall(GameTooltip.SetUnit, GameTooltip, s.unit) end
    GameTooltip:AddLine("Buttons cast on this person. Card: right-click Rejuvenation · Shift Regrowth · Ctrl Healing Touch · Alt Cure Poison", 0.5, 0.83, 0.36, true)
    GameTooltip:Show()
  end)
  b:SetScript("OnLeave", function() GameTooltip:Hide() end)
  return b
end

local function makePet(i, unit, owner)
  local p = CreateFrame("Button", "DruidKitPartyPet" .. i, container, "SecureUnitButtonTemplate")
  p:SetSize(CARD_W - PORTRAIT - 30, PET_H)
  p:SetPoint("TOPRIGHT", owner, "BOTTOMRIGHT", 0, -2)
  p:RegisterForClicks("AnyUp")
  p:SetAttribute("unit", unit)
  p:SetAttribute("type1", "target")
  p:SetAttribute("type2", "spell"); p:SetAttribute("spell2", "Rejuvenation")
  p:SetAttribute("shift-type1", "spell");  p:SetAttribute("shift-spell1", "Regrowth")
  p:SetAttribute("ctrl-type1", "spell");   p:SetAttribute("ctrl-spell1", "Healing Touch")
  p:SetAttribute("alt-type1", "spell");    p:SetAttribute("alt-spell1", "Cure Poison")
  p.unit = unit
  p.hp = CreateFrame("StatusBar", nil, p); p.hp:SetAllPoints()
  p.hp:SetStatusBarTexture(BAR_TEX); p.hp:SetStatusBarColor(LEAF[1], LEAF[2], LEAF[3], 0.9)
  p.hp.bg = p.hp:CreateTexture(nil, "BACKGROUND"); p.hp.bg:SetAllPoints(); p.hp.bg:SetColorTexture(0.05, 0.05, 0.05, 0.9)
  p.name = text(p.hp, 13); p.name:SetPoint("LEFT", 6, 0)
  -- Pet heal set: three small buttons on the right of the bar, cast on this pet.
  p.heals = {}
  local PET_SPELLS = { "Rejuvenation", "Regrowth", "Healing Touch" }
  for n = #PET_SPELLS, 1, -1 do
    local sp = PET_SPELLS[n]
    local h = CreateFrame("Button", nil, p, "SecureActionButtonTemplate")
    h:SetSize(PET_H - 2, PET_H - 2)
    h:SetPoint("RIGHT", p, "RIGHT", -1 - (#PET_SPELLS - n) * PET_H, 0)
    h:RegisterForClicks("AnyUp", "AnyDown")
    h:SetAttribute("type", "spell"); h:SetAttribute("spell", sp); h:SetAttribute("unit", unit)
    h:SetFrameLevel(p:GetFrameLevel() + 3)
    h.tex = h:CreateTexture(nil, "ARTWORK"); h.tex:SetAllPoints(); h.tex:SetTexCoord(0.08, 0.92, 0.08, 0.92)
    local icon = (C_Spell and C_Spell.GetSpellTexture and C_Spell.GetSpellTexture(sp)) or (GetSpellTexture and GetSpellTexture(sp))
    h.tex:SetTexture(icon or "Interface\\Icons\\Spell_Nature_Rejuvenation")
    local hl = h:CreateTexture(nil, "HIGHLIGHT"); hl:SetAllPoints(); hl:SetColorTexture(1, 1, 1, 0.3)
    h:SetScript("OnEnter", function(s) GameTooltip:SetOwner(s, "ANCHOR_TOP"); GameTooltip:AddLine(sp .. " on the pet", 1, 1, 1); GameTooltip:Show() end)
    h:SetScript("OnLeave", function() GameTooltip:Hide() end)
    p.heals[#p.heals + 1] = h
  end
  p.tag = text(p.hp, 13); p.tag:SetPoint("RIGHT", -6 - #PET_SPELLS * PET_H, 0); p.tag:SetText("PET")
  p:SetScript("OnEnter", function(s)
    GameTooltip:SetOwner(s, "ANCHOR_TOP")
    GameTooltip:AddLine("Pet: click to target · Right-click Rejuvenation · Shift Regrowth · Ctrl Healing Touch · Alt Cure Poison", 1, 1, 1, true)
    GameTooltip:Show()
  end)
  p:SetScript("OnLeave", function() GameTooltip:Hide() end)
  return p
end
local function setPetUnit(p, u)
  p:SetAttribute("unit", u); p.unit = u
  for _, h in ipairs(p.heals or {}) do h:SetAttribute("unit", u) end
end

-- Spell buttons: which action slot each one uses (only changed out of combat) ---------
local function applySlots()
  if InCombatLockdown() then slotsDirty = true; return end
  local list = findCardSlots()
  for _, b in ipairs(cards) do
    for n, s in ipairs(b.btns) do
      local e = list[n]
      if e then
        s.slot, s.spell = e.slot, e.name
        s:SetAttribute("action", e.slot)
        s:SetAttribute("unit", b.unit)
        s.tex:SetTexture(actionTexture(e.slot))
        s.badge:SetText((e.name == "Cure Poison" or e.name == "Abolish Poison") and "P" or (e.name == "Remove Curse" and "C" or ""))
        s:SetAlpha(1); s:EnableMouse(true)
      else
        s.slot, s.spell = nil, nil
        s:SetAttribute("action", nil)
        s:SetAlpha(0); s:EnableMouse(false)
      end
    end
  end
  slotsDirty = false
end

-- Update -----------------------------------------------------------------------------
local function setPulse(b, on)
  if on then if not b.pulse:IsPlaying() then b.pulse:Play() end
  else if b.pulse:IsPlaying() then b.pulse:Stop() end; b.glow:SetAlpha(0) end
end

local function updatePortrait(b)
  local unit = b.unit
  if not UnitExists(unit) then return end
  if try(UnitIsVisible, unit) ~= false and SetPortraitTexture then
    b.portrait:SetTexCoord(0, 1, 0, 1)
    pcall(SetPortraitTexture, b.portrait, unit)
  else
    local _, class = try(UnitClass, unit)
    local tc = class and CLASS_ICON_TCOORDS and CLASS_ICON_TCOORDS[class]
    if tc then
      b.portrait:SetTexture("Interface\\Glues\\CharacterCreate\\UI-CharacterCreate-Classes")
      b.portrait:SetTexCoord(tc[1], tc[2], tc[3], tc[4])
    end
  end
end

local function updateButtons(b, poison, curse)
  for _, s in ipairs(b.btns) do
    if s.slot then
      pcall(setCooldown, s.cd, s.slot)
      local usable, noMana = try(IsUsableAction, s.slot)
      usable, noMana = plain(usable), plain(noMana)
      if usable == false and noMana then s.tex:SetVertexColor(0.4, 0.4, 1)        -- out of mana: blue-grey
      elseif usable == false then s.tex:SetVertexColor(0.45, 0.45, 0.45)
      else s.tex:SetVertexColor(1, 1, 1) end
      local want = (poison and (s.spell == "Cure Poison" or s.spell == "Abolish Poison")) or (curse and s.spell == "Remove Curse")
      if want then if not s.pulse:IsPlaying() then s.pulse:Play() end
      elseif s.pulse:IsPlaying() then s.pulse:Stop(); s:SetAlpha(1) end
    end
  end
end

-- Health and mana can be hidden ("secret") values: never test or do maths on them directly.
-- Bars and text take them as they are; percentages only when the numbers are readable.
local function setBar(bar, cur, max)
  pcall(bar.SetMinMaxValues, bar, 0, max)
  pcall(bar.SetValue, bar, cur)
end
local function short(n)
  if n >= 10000 then return ("%.1fk"):format(n / 1000) end
  return tostring(math.floor(n + 0.5))
end
local function setNumbers(fs, cur, max)
  local c, m = plain(cur), plain(max)
  if c and m then fs:SetText(short(c) .. " / " .. short(m)); return end
  -- hidden values: let the game print them
  if not pcall(fs.SetFormattedText, fs, "%s / %s", cur, max) then fs:SetText("") end
end

local function part(fn, ...) local ok, err = pcall(fn, ...); if not ok then logErr("update", err) end return ok end

local function updateCard(b)
  local unit = b.unit
  if not UnitExists(unit) then return end
  -- name + class colour
  part(function()
    local name = UnitName(unit)
    if not pcall(b.name.SetText, b.name, name) then b.name:SetText("") end
    local _, class = UnitClass(unit)
    class = plain(class)
    local c = class and RAID_CLASS_COLORS and RAID_CLASS_COLORS[class]
    if not c then c = { r = 0.5, g = 0.83, b = 0.36 } end
    b.name:SetTextColor(c.r, c.g, c.b)
    b.stripe:SetColorTexture(c.r, c.g, c.b, 1)
    b.hp:SetStatusBarColor(LEAF[1], LEAF[2], LEAF[3])
    b.classColor = c
    local lvl = plain(UnitLevel(unit))
    b.level.t:SetText(lvl and lvl > 0 and tostring(lvl) or "")
  end)
  -- bars and numbers
  part(function()
    local cur, max = UnitHealth(unit), UnitHealthMax(unit)
    setBar(b.hp, cur, max); setNumbers(b.hpText, cur, max)
  end)
  part(function()
    local cur, max = UnitPower(unit), UnitPowerMax(unit)
    setBar(b.mp, cur, max)
    local c, m = plain(cur), plain(max)
    b.mpText:SetText((c and m and m > 0) and (short(c) .. " / " .. short(m)) or "")
    local ptype = plain(UnitPowerType(unit))
    if ptype == 1 then b.mp:SetStatusBarColor(0.85, 0.2, 0.2) elseif ptype == 3 then b.mp:SetStatusBarColor(0.95, 0.85, 0.25)
    else b.mp:SetStatusBarColor(0.2, 0.5, 1) end
  end)

  local dead = plain(try(UnitIsDeadOrGhost, unit)) == true
  local inRange = plain(try(UnitInRange, unit))
  b:SetAlpha((unit ~= "player" and inRange == false) and 0.5 or 1)

  part(function()
    for h, spell in ipairs(MY_HOTS) do
      local a = auraByName(unit, spell, "HELPFUL|PLAYER")
      local ic = b.hots[h]
      if a then
        ic.tex:SetTexture(plain(a.icon) or "Interface\\Icons\\Spell_Nature_Rejuvenation")
        local exp = plain(a.expirationTime)
        ic.txt:SetText(exp and exp > 0 and math.max(0, math.floor(exp - GetTime() + 0.5)) or "")
        ic:Show()
      else ic:Hide() end
    end
  end)

  local poison, curse = false, false
  part(function()
    local knowsMotW = knownSpell("Mark of the Wild")
    showFix(b.motw, knowsMotW and not dead and not auraByName(unit, "Mark of the Wild", "HELPFUL") and not auraByName(unit, "Gift of the Wild", "HELPFUL"), false)
    local knowsThorns = knownSpell("Thorns")
    local tanking = plain(try(UnitGroupRolesAssigned, unit)) == "TANK" or (plain(try(UnitThreatSituation, unit)) or 0) >= 2
    showFix(b.thorns, knowsThorns and tanking and not dead and not auraByName(unit, "Thorns", "HELPFUL"), false)
    showFix(b.res, dead and unit ~= "player", true)
    if C_UnitAuras and C_UnitAuras.GetAuraDataByIndex and not dead then
      for i = 1, 40 do
        local a = try(C_UnitAuras.GetAuraDataByIndex, unit, i, "HARMFUL")
        if not a then break end
        local k = plain(a.dispelName)
        if k == "Poison" then poison = true elseif k == "Curse" then curse = true end
      end
    end
    showFix(b.cureP, poison, true)
    showFix(b.cureC, curse, true)
  end)
  part(updateButtons, b, poison, curse)

  part(function()
    local threat = plain(UnitThreatSituation(unit)) or 0
    local aggro = threat >= 2 and plain(UnitGroupRolesAssigned(unit)) ~= "TANK" and unit ~= "player" and not dead
    b.aggro:SetShown(aggro)
  end)

  part(function()
    local frac = healthFrac(unit)
    b.portrait:SetDesaturated(dead)
    if dead then
      b.state:SetText("|cffd0d0d0DEAD|r"); b.big:SetText(unit == "player" and "DEAD" or "")
      b.hp:SetStatusBarColor(0.3, 0.3, 0.3); setPulse(b, false)
    elseif frac and frac < CRITICAL then
      b.state:SetText(("|cffffffff!! %d%%|r"):format(math.floor(frac * 100 + 0.5))); b.big:SetText("!!")
      setPulse(b, true)
    else
      b.big:SetText("")
      if frac and frac < LOW then b.state:SetText(("|cffffd100LOW %d%%|r"):format(math.floor(frac * 100 + 0.5)))
      elseif frac then b.state:SetText(("|cffffffff%d%%|r"):format(math.floor(frac * 100 + 0.5)))
      elseif UnitHealthPercent and pcall(b.state.SetFormattedText, b.state, "%d%%", UnitHealthPercent(unit, true, CurveConstants and CurveConstants.ScaleTo100)) then
        -- hidden values: the game prints the percent for us
      else b.state:SetText("") end
      setPulse(b, false)
    end
  end)
  part(function() b.selEdge:SetShown(UnitIsUnit("target", unit) == true) end)
end

local function updatePet(p)
  if not UnitExists(p.unit) then return end
  setBar(p.hp, UnitHealth(p.unit), UnitHealthMax(p.unit))
  if not pcall(p.name.SetText, p.name, UnitName(p.unit)) then p.name:SetText("") end
  local frac = healthFrac(p.unit)
  if plain(try(UnitIsDeadOrGhost, p.unit)) == true then p.tag:SetText("DEAD")
  elseif frac and frac < CRITICAL then p.tag:SetText(("!! %d%%"):format(math.floor(frac * 100 + 0.5)))
  elseif frac and frac < LOW then p.tag:SetText(("LOW %d%%"):format(math.floor(frac * 100 + 0.5)))
  else p.tag:SetText("PET") end
end

local function updateAll()
  if not container or not container:IsShown() then return end
  for _, b in ipairs(cards) do if b:IsShown() then local ok, e = pcall(updateCard, b); if not ok then logErr("updateCard", e) end end end
  for _, p in ipairs(pets) do if p:IsShown() then pcall(updatePet, p) end end
end
local function updatePortraits() for _, b in ipairs(cards) do if b:IsShown() then pcall(updatePortrait, b) end end end

-- Showing / hiding (secure, so it works in combat) --------------------------------------
local function setUnits(fn)
  for i, b in ipairs(cards) do
    local u = fn(i, UNITS[i])
    b:SetAttribute("unit", u); b.unit = u
    for _, f in ipairs({ b.motw, b.cureP, b.cureC, b.thorns, b.res }) do f:SetAttribute("unit", u) end
    b.res:SetAttribute("macrotext", ("/cast [@%s,combat] Rebirth; [@%s] Revive"):format(u, u))
    for _, s in ipairs(b.btns) do s:SetAttribute("unit", u) end
  end
end
local function setLive()
  setUnits(function(_, u) return u end)
  for _, b in ipairs(cards) do RegisterUnitWatch(b) end
  for i, p in ipairs(pets) do setPetUnit(p, PETS[i]); RegisterUnitWatch(p) end
  if DB.partyOn then RegisterStateDriver(container, "visibility", "[group:party] show; hide")
  else RegisterStateDriver(container, "visibility", "hide") end
end

local function setTest(on)
  if InCombatLockdown() then say("can't change that in combat.") return end
  if #cards == 0 then say("the party view didn't build. Type /reload, then tell Claude 'update' so it can read the error."); return end
  testing = on
  if on then
    UnregisterStateDriver(container, "visibility")
    for _, b in ipairs(cards) do UnregisterUnitWatch(b); b:Show() end
    setUnits(function() return "player" end)
    for _, p in ipairs(pets) do UnregisterUnitWatch(p); setPetUnit(p, "player"); p:Show() end
    container:Show()
    say("party preview on (5 copies of you). /dk unlock to drag it, /dk party test again to close.")
  else
    setLive()
    say("party preview off.")
  end
  local okS, eS = pcall(applySlots); if not okS then logErr("applySlots", eS) end
  updatePortraits(); updateAll()
end

local function applyScale()
  if InCombatLockdown() then return end
  local sc = SIZES[DB.partySize or "normal"] or 1
  -- normal fits the left third of the screen (the middle stays clear); never bigger than the screen allows
  local uw, uh = UIParent:GetWidth() or 0, UIParent:GetHeight() or 0
  local w, h = container:GetWidth() or 1, container:GetHeight() or 1
  if uw > 0 and uh > 0 then sc = math.min(sc * math.min(1, (uw / 3 - 20) / w), (uw * 0.62) / w, (uh * 0.85) / h) end
  container:SetScale(sc)
  if DruidKitPos then DruidKitPos.place(container, "party") end
end

local handle
local function setMovable(on)
  if not container or InCombatLockdown() then return end
  if on then
    if not handle then
      handle = CreateFrame("Frame", nil, container, "BackdropTemplate")
      handle:SetPoint("BOTTOMLEFT", container, "TOPLEFT", 0, 4); handle:SetPoint("BOTTOMRIGHT", container, "TOPRIGHT", 0, 4)
      handle:SetHeight(22)
      if handle.SetBackdrop then handle:SetBackdrop({ bgFile = "Interface\\Buttons\\WHITE8x8" }); handle:SetBackdropColor(ORANGE[1], ORANGE[2], ORANGE[3], 0.6) end
      handle.t = text(handle, 13); handle.t:SetPoint("CENTER"); handle.t:SetText("Drag to move the party view")
      handle:EnableMouse(true); handle:RegisterForDrag("LeftButton")
      handle:SetScript("OnDragStart", function() container:StartMoving() end)
      handle:SetScript("OnDragStop", function()
        container:StopMovingOrSizing()
        if DruidKitPos then DruidKitPos.save(container, "party") end
      end)
    end
    handle:Show()
    if not testing then setTest(true) end
  else
    if handle then handle:Hide() end
    if testing then setTest(false) end
  end
end
DruidKit_PartyMovable = setMovable

-- Build ---------------------------------------------------------------------------------
local function build()
  container = CreateFrame("Frame", "DruidKitParty", UIParent)
  container:SetSize(COLS * CARD_W + (COLS - 1) * GAP, HEADER_H + ROWS * (CARD_H + PET_H + GAP + 2))
  -- title strip: leaf icon + "Party", bark and gold
  local hd = CreateFrame("Frame", nil, container, "BackdropTemplate")
  hd:SetPoint("TOPLEFT", 0, 0); hd:SetPoint("TOPRIGHT", 0, 0); hd:SetHeight(HEADER_H - 4)
  if hd.SetBackdrop then
    hd:SetBackdrop({ bgFile = BAR_TEX, edgeFile = "Interface\\Tooltips\\UI-Tooltip-Border", edgeSize = 12, insets = { left = 3, right = 3, top = 3, bottom = 3 } })
    hd:SetBackdropColor(BARK[1] * 0.5, BARK[2] * 0.5, BARK[3] * 0.5, 0.95); hd:SetBackdropBorderColor(GOLD[1], GOLD[2], GOLD[3], 1)
  end
  local ic = hd:CreateTexture(nil, "ARTWORK"); ic:SetSize(16, 16); ic:SetPoint("LEFT", 8, 0); ic:SetTexture("Interface\\Icons\\Spell_Nature_Rejuvenation"); ic:SetTexCoord(0.08, 0.92, 0.08, 0.92)
  local tt = text(hd, 13); tt:SetPoint("LEFT", ic, "RIGHT", 6, 0); tt:SetText("Party"); tt:SetTextColor(GOLD[1], GOLD[2], GOLD[3])
  local hint = text(hd, 13); hint:SetPoint("RIGHT", -10, 0); hint:SetText("click a button to cast it on that person"); hint:SetTextColor(0.75, 0.75, 0.65)
  if DruidKitPos then DruidKitPos.place(container, "party") end
  container:SetMovable(true); container:SetClampedToScreen(true)
  container:Hide()
  for i, unit in ipairs(UNITS) do
    local ok, c = pcall(makeCard, i, unit)
    if ok then cards[#cards + 1] = c else say("party card " .. i .. " failed: " .. tostring(c)); logErr("makeCard " .. i, c); return end
  end
  for i, unit in ipairs(PETS) do
    local ok, p = pcall(makePet, i, unit, cards[i])
    if ok then pets[#pets + 1] = p else say("party pet bar failed: " .. tostring(p)); logErr("makePet " .. i, p) end
  end
  applyScale()
  setLive()
  local okS, eS = pcall(applySlots); if not okS then logErr("applySlots", eS) end
end

-- Unit events come for every unit (target, nameplates...): only ours mark the cards dirty; OnUpdate draws them.
local WATCHED = {}
for _, u in ipairs(UNITS) do WATCHED[u] = true end
for _, u in ipairs(PETS) do WATCHED[u] = true end
local dirty = false
local ev = CreateFrame("Frame")
for _, e in ipairs({ "PLAYER_LOGIN", "PLAYER_ENTERING_WORLD", "GROUP_ROSTER_UPDATE", "UNIT_HEALTH", "UNIT_MAXHEALTH", "UNIT_POWER_UPDATE",
                     "UNIT_AURA", "UNIT_THREAT_SITUATION_UPDATE", "UNIT_PET", "PLAYER_TARGET_CHANGED", "PLAYER_REGEN_ENABLED",
                     "PLAYER_REGEN_DISABLED",
                     "UNIT_PORTRAIT_UPDATE", "UNIT_MODEL_CHANGED", "ACTIONBAR_SLOT_CHANGED", "SPELL_UPDATE_COOLDOWN",
                     "ACTIONBAR_UPDATE_COOLDOWN", "ACTIONBAR_UPDATE_USABLE" }) do
  pcall(ev.RegisterEvent, ev, e)
end
ev:SetScript("OnEvent", function(_, e, unit)
  if e:sub(1, 5) == "UNIT_" and not WATCHED[unit] then return end
  if e == "PLAYER_LOGIN" then
    DruidKitDB = DruidKitDB or {}
    DB = DruidKitDB
    if DB.partyOn == nil then DB.partyOn = true end
    DB.partyLog = {}
    local ok, err = pcall(build)
    if not ok then say("party view failed to load: " .. tostring(err)); logErr("build", err) end
    DB.partyBuilt = { cards = #cards, pets = #pets, at = (date and date("%H:%M:%S") or "") }
    return
  end
  if not container then return end
  if e == "ACTIONBAR_SLOT_CHANGED" then slotsDirty = true end
  if e == "PLAYER_REGEN_DISABLED" then combatReady() return end
  if e == "PLAYER_REGEN_ENABLED" then afterCombat() end
  if e == "PLAYER_REGEN_ENABLED" or e == "ACTIONBAR_SLOT_CHANGED" or e == "PLAYER_ENTERING_WORLD" then
    if slotsDirty then applySlots() end
  end
  if e == "GROUP_ROSTER_UPDATE" or e == "UNIT_PORTRAIT_UPDATE" or e == "UNIT_MODEL_CHANGED" or e == "PLAYER_ENTERING_WORLD" then
    C_Timer.After(0.2, updatePortraits)
  end
  dirty = true
end)
-- Changes are drawn within 0.1 s; HoT countdowns, range and cooldowns twice a second anyway; portraits every 5 s
local acc, pacc = 0, 0
ev:SetScript("OnUpdate", function(_, el)
  acc, pacc = acc + el, pacc + el
  if acc < (dirty and 0.1 or 0.5) then return end
  acc, dirty = 0, false
  if container and container:IsShown() then
    updateAll()
    if pacc > 5 then pacc = 0; updatePortraits() end
  end
end)

function DruidKit_PartyCommand(arg)
  if not container then return end
  local a, b = (arg or ""):match("^(%S*)%s*(.-)$")
  if a == "test" then setTest(not testing)
  elseif a == "off" or a == "on" then
    if InCombatLockdown() then say("can't change that in combat.") return end
    DB.partyOn = (a == "on"); setLive()
    say("party view " .. (DB.partyOn and "on (shows in a party)." or "off."))
  elseif a == "size" and SIZES[b] then
    if InCombatLockdown() then say("can't change that in combat.") return end
    DB.partySize = b; applyScale(); say("party view size: " .. b .. ".")
  elseif a == "reset" then
    if DruidKitPos then DruidKitPos.reset("party") end
  else
    say("/dk party test · on · off · size small|normal|big · reset")
  end
end
