-- Druid Kit helpers: catch-up tracker, pre-pull check, level-up assistant, rest prompt.
-- Information and reminders only; nothing here plays for you.
--   /dk catchup [level]   set the level you're catching up to (blank = highest friend seen)
--   /dk hud on|off        pre-pull check row
--   /dk rest on|off       rest prompt
--   /dk tracker on|off    catch-up tracker
--   /dk unlock | lock     drag the panels where you want them

local DRUID, LEAF, RED, GREY = "|cffff7c0a", "|cff7fd35b", "|cffff6060", "|cff9d9d9d"
local function safe(fn, ...)
  if not fn then return nil end
  local ok, a, b, c, d, e, f, g, h = pcall(fn, ...)
  if ok then return a, b, c, d, e, f, g, h end
end
local function say(msg) print("|cff7fd35bDruid Kit:|r " .. msg) end
local function shout(msg, r, g, b)
  if RaidNotice_AddMessage and RaidWarningFrame and ChatTypeInfo then
    pcall(RaidNotice_AddMessage, RaidWarningFrame, msg, { r = r or 1, g = g or 0.49, b = b or 0.04 })
  elseif UIErrorsFrame then
    UIErrorsFrame:AddMessage(msg, r or 1, g or 0.49, b or 0.04)
  end
end

local DB
local function opt(key, default)
  if DB[key] == nil then DB[key] = default end
  return DB[key]
end

-- XP needed to go from level N to N+1 (matches WoW Forever: level 12 needs 10,100).
local XP_TO_NEXT = {
  400, 900, 1400, 2100, 2800, 3600, 4500, 5400, 6500, 7600,
  8800, 10100, 11400, 12900, 14400, 16000, 17700, 19400, 21300, 23200,
  25200, 27300, 29400, 31700, 34000, 36400, 38900, 41400, 44300, 47400,
  50800, 54100, 57500, 61000, 64600, 68300, 72100, 76000, 80000, 84100,
  88300, 92600, 97000, 101500, 106100, 110800, 115600, 120500, 125500, 130600,
  135800, 141100, 146500, 152000, 157700, 163400, 169300, 175300, 181400,
}

local function spellID(name)
  if C_Spell and C_Spell.GetSpellInfo then
    local i = safe(C_Spell.GetSpellInfo, name)
    if type(i) == "table" then return i.spellID end
  end
  if GetSpellInfo then local _, _, _, _, _, _, id = safe(GetSpellInfo, name); return id end
end
local function known(name)
  local id = spellID(name)
  if not id then return false end
  if C_SpellBook and C_SpellBook.IsSpellKnown then return safe(C_SpellBook.IsSpellKnown, id) and true or false end
  if IsPlayerSpell then return safe(IsPlayerSpell, id) and true or false end
  return true
end
local function spellIcon(name)
  local id = spellID(name)
  if C_Spell and C_Spell.GetSpellTexture then return safe(C_Spell.GetSpellTexture, id or name) end
  if GetSpellTexture then return safe(GetSpellTexture, id or name) end
end
local function hasBuffRaw(name)
  if C_UnitAuras and C_UnitAuras.GetAuraDataBySpellName then
    if safe(C_UnitAuras.GetAuraDataBySpellName, "player", name, "HELPFUL") then return true end
  end
  for i = 1, 40 do
    local n
    if C_UnitAuras and C_UnitAuras.GetBuffDataByIndex then
      local d = safe(C_UnitAuras.GetBuffDataByIndex, "player", i); n = d and d.name
    elseif UnitBuff then n = safe(UnitBuff, "player", i) end
    if not n then return false end
    if n == name then return true end
  end
  return false
end
local function hasBuff(name)
  local ok, r = pcall(hasBuffRaw, name)
  return ok and r or false
end
-- WoW Forever can hide exact health and mana from addons ("secret" values). Then these return nil
-- and the panels fall back to plain bars, which the game is happy to fill in for us.
local function plain(v)
  if v == nil then return nil end
  if issecretvalue and issecretvalue(v) then return nil end
  return v
end
local function pct(cur, max)
  cur, max = plain(cur), plain(max)
  if not cur or not max then return nil end
  if max <= 0 then return 100 end
  return math.floor(cur / max * 100)
end
local function healthPct() return pct(UnitHealth("player"), UnitHealthMax("player")) end
local function manaPct() return pct(UnitPower("player", 0), UnitPowerMax("player", 0)) end
local function fillBar(bar, cur, max)
  pcall(bar.SetMinMaxValues, bar, 0, max or 1)
  pcall(bar.SetValue, bar, cur or 0)
end

-- Movable panels -------------------------------------------------------------
local panels = {}
local function makePanel(key, w, h, point, x, y)
  local f = CreateFrame("Frame", "DruidKit_" .. key, UIParent, BackdropTemplateMixin and "BackdropTemplate" or nil)
  f:SetSize(w, h)
  local p = DB.panels and DB.panels[key]
  if p then f:SetPoint(p[1], UIParent, p[2], p[3], p[4]) else f:SetPoint(point, UIParent, point, x, y) end
  f:SetMovable(true); f:SetClampedToScreen(true)
  f:RegisterForDrag("LeftButton")
  f:SetScript("OnDragStart", f.StartMoving)
  f:SetScript("OnDragStop", function()
    f:StopMovingOrSizing()
    local a, _, b, px, py = f:GetPoint(1)
    DB.panels = DB.panels or {}
    DB.panels[key] = { a, b, px, py }
  end)
  if f.SetBackdrop then
    f:SetBackdrop({ bgFile = "Interface\\Tooltips\\UI-Tooltip-Background", edgeFile = "Interface\\Tooltips\\UI-Tooltip-Border", edgeSize = 12, insets = { left = 3, right = 3, top = 3, bottom = 3 } })
    f:SetBackdropColor(0.03, 0.10, 0.04, 0.80)
    f:SetBackdropBorderColor(1, 0.49, 0.04, 0.6)
  end
  panels[key] = f
  return f
end
local function setUnlocked(on)
  for _, f in pairs(panels) do f:EnableMouse(on); if on then f:Show() end end
  say(on and "panels unlocked: drag them, then /dk lock." or "panels locked.")
end

-- 1. Catch-up tracker ---------------------------------------------------------
local tracker, trackerText
local samples, lastXP, lastMax = {}, nil, nil

-- Friends (saved, the default catch-up target) and guild members (this session only: /dk catchup <name> finds them).
local guild = {}
local function friendLevels()
  DB.friends = DB.friends or {}
  local isFriend = {}
  if C_FriendList and C_FriendList.GetNumFriends then
    for i = 1, (safe(C_FriendList.GetNumFriends) or 0) do
      local f = safe(C_FriendList.GetFriendInfoByIndex, i)
      if f and f.name then isFriend[f.name] = true end
      if f and f.name and f.level and f.level > 0 then DB.friends[f.name] = f.level end
    end
  end
  if BNGetNumFriends and C_BattleNet and C_BattleNet.GetFriendAccountInfo then
    for i = 1, (safe(BNGetNumFriends) or 0) do
      local a = safe(C_BattleNet.GetFriendAccountInfo, i)
      local g = a and a.gameAccountInfo
      if g and g.clientProgram == "WoW" and g.characterName then
        isFriend[g.characterName] = true
        if (g.characterLevel or 0) > 0 then DB.friends[g.characterName] = g.characterLevel end
      end
    end
  end
  if IsInGuild and IsInGuild() and GetNumGuildMembers then
    for i = 1, (safe(GetNumGuildMembers) or 0) do
      local name, _, _, level = safe(GetGuildRosterInfo, i)
      if name and level then
        name = name:match("^[^-]+") or name
        guild[name] = level
        if not isFriend[name] then DB.friends[name] = nil end   -- saved by older versions
      end
    end
  end
end

-- A named friend wins over everything else (partial names are fine: "ali" finds Alistair).
local function findFriend(pattern)
  if not pattern then return end
  pattern = pattern:lower()
  for _, list in ipairs({ DB.friends or {}, guild }) do
    for name, lvl in pairs(list) do
      if name:lower():sub(1, #pattern) == pattern then return lvl, name end
    end
  end
end

local function targetLevel()
  if DB.catchupFriend then
    local lvl, name = findFriend(DB.catchupFriend)
    if lvl then return lvl, name, true end
    return DB.catchupTarget, DB.catchupTarget and "Target" or nil, false, "missing"
  end
  if DB.catchupTarget then return DB.catchupTarget, "Target" end
  local best, who = nil, nil
  for name, lvl in pairs(DB.friends or {}) do
    if lvl <= 60 and (not best or lvl > best) then best, who = lvl, name end
  end
  return best, who
end

local function xpRate()
  local now, total, oldest = GetTime(), 0, nil
  for i = #samples, 1, -1 do
    if now - samples[i].t > 3600 then table.remove(samples, i) end
  end
  for _, s in ipairs(samples) do total = total + s.xp; oldest = oldest and math.min(oldest, s.t) or s.t end
  if not oldest then return 0 end
  local span = math.max(now - (DB.sessionStart or oldest), 300)
  span = math.min(span, 3600)
  return total / span * 3600
end

local function fmtTime(hours)
  if not hours or hours ~= hours or hours == math.huge then return "\226\128\148" end
  if hours < 1 then return ("%dm"):format(math.max(1, math.floor(hours * 60))) end
  return ("%dh %02dm"):format(math.floor(hours), math.floor((hours % 1) * 60))
end

-- Professions: say when to train the next rank so skill-ups are never wasted at the cap.
local JOURNEYMAN = {
  ["Alchemy"]   = "Lilyssia Nightbreeze, Stormwind Mage Quarter (or Sylvanna Forestmoon, Darnassus)",
  ["First Aid"] = "Shaina Fuller, Stormwind (or Dannelor, Darnassus)",
  ["Cooking"]   = "Stephen Ryback, Stormwind (or Alegorn, Darnassus)",
  ["Fishing"]   = "Arnold Leland, Stormwind canals (or Androl Oakhand, Rut'theran)",
  ["Herbalism"] = "Malvor, Moonglade",
}
local EXPERT = {
  ["First Aid"] = "buy Expert First Aid - Under Wraps from Deneb Walker, Arathi (First Aid 125)",
  ["Cooking"]   = "buy the Expert Cookbook from Shandrina, Mystral Lake, Ashenvale (Cooking 125, level 20)",
  ["Fishing"]   = "read Expert Fishing - The Bass and You, Booty Bay (Fishing 125, level 20)",
  ["Alchemy"]   = "Expert rank at an Expert trainer, e.g. Lilyssia Nightbreeze, Stormwind (Alchemy 125, level 20)",
  ["Herbalism"] = "Expert rank at a Herbalism trainer (Herbalism 125)",
}
local function professionLines()
  local out = {}
  if not GetNumSkillLines or not GetSkillLineInfo then return out end
  for i = 1, (GetNumSkillLines() or 0) do
    local name, header, _, rank, _, _, max = GetSkillLineInfo(i)
    if name and not header and rank and max and (JOURNEYMAN[name] or EXPERT[name]) then
      if max == 75 and rank >= 50 and JOURNEYMAN[name] then
        table.insert(out, DRUID .. "! Train|r " .. name .. (" %d/75: "):format(rank) .. GREY .. JOURNEYMAN[name] .. "|r")
      elseif max == 150 and rank >= 125 and EXPERT[name] then
        table.insert(out, DRUID .. "! Expert|r " .. name .. (" %d/150: "):format(rank) .. GREY .. EXPERT[name] .. "|r")
      elseif max > 0 and rank >= max then
        table.insert(out, DRUID .. "! Capped|r " .. name .. (" %d/%d: train the next rank"):format(rank, max))
      end
    end
  end
  return out
end
DruidKit_ProfessionLines = professionLines

-- Gold towards the first mount: the same per-level target as Bag check's mount money line (DruidKit_MountTarget).
local function goldLine()
  local lvl = UnitLevel("player") or 1
  if lvl >= 40 or not (GetMoney and DruidKit_MountTarget) then return nil end
  local copper = plain(GetMoney()); if not copper then return nil end
  local full, target = DruidKit_MountTarget(40), DruidKit_MountTarget(lvl)
  local function g(c) return math.floor(c / 10000) end
  if copper >= full then return LEAF .. ("Mount fund ready|r: %dg for riding at 40."):format(g(full)) end
  local head = ("%sGold|r %dg %ds · mount at 40 = %dg"):format(DRUID, g(copper), math.floor(copper / 100) % 100, g(full))
  if target == 0 then return head .. ": start saving" end
  if copper >= target then return head .. (": on track (aim %dg at %d)"):format(g(target), lvl) end
  return head .. (": BEHIND by %dg (aim %dg at %d)"):format(math.ceil((target - copper) / 10000), g(target), lvl)
end
DruidKit_GoldLine = goldLine

local function updateTracker()
  if not tracker or not DB.trackerOn then return end
  local lvl, cur, max = UnitLevel("player"), UnitXP("player"), UnitXPMax("player")
  local rate = xpRate()
  local toLevel = (rate > 0) and ((max - cur) / rate) or nil
  local lines = { DRUID .. "Catch-up|r  " .. GREY .. ("Lv %d, %d%%"):format(lvl, pct(cur, max)) .. "|r" }
  table.insert(lines, ("XP/hour: %s   Next level: %s"):format(rate > 0 and LEAF .. BreakUpLargeNumbers(math.floor(rate)) .. "|r" or GREY .. "warming up|r", fmtTime(toLevel)))
  local target, who = targetLevel()
  local _, _, isFriend, missing = targetLevel()
  if missing then
    table.insert(lines, GREY .. ("%s not on your friends list yet: add them by BattleTag (O, Add Friend).|r"):format(DB.catchupFriend:gsub("^%l", string.upper)))
  end
  if target and target > lvl then
    local need = max - cur
    for l = lvl + 1, target - 1 do need = need + (XP_TO_NEXT[l] or 0) end
    table.insert(lines, ("%s %d: %d levels behind, %s"):format(who or "Friends", target, target - lvl, rate > 0 and ("about " .. fmtTime(need / rate)) or "pace unknown"))
    if isFriend then
      local gap = target - lvl
      if gap >= 8 then
        table.insert(lines, GREY .. "Big gap: kills together give you little XP. Do dungeon quests with him.|r")
      elseif gap >= 4 then
        table.insert(lines, GREY .. "Getting close: group for his yellow/orange mobs and dungeon quests.|r")
      else
        table.insert(lines, LEAF .. "Close enough to level together!|r")
        table.insert(lines, GREY .. "Keep levelling as Feral; pick a new build at 60 (Talents tab).|r")
      end
    end
  elseif target then
    table.insert(lines, LEAF .. ("Caught up with %s (%d)!"):format(who or "your friends", target) .. "|r")
    table.insert(lines, GREY .. "Keep levelling as Feral; pick a new build at 60 (Talents tab).|r")
  else
    table.insert(lines, GREY .. "Add your friends, or /dk catchup 22|r")
  end
  local okP, pl = pcall(professionLines)
  if okP then for _, l in ipairs(pl) do table.insert(lines, l) end end
  local okG, gl = pcall(goldLine)
  if okG and gl then table.insert(lines, gl) end
  trackerText:SetText(table.concat(lines, "\n"))
  tracker:SetHeight(trackerText:GetStringHeight() + 14)
  tracker:Show()
end

local function onXP()
  local cur, max = UnitXP("player"), UnitXPMax("player")
  if lastXP then
    local gained = (cur >= lastXP) and (cur - lastXP) or ((lastMax or 0) - lastXP + cur)
    if gained > 0 then table.insert(samples, { t = GetTime(), xp = gained }) end
  end
  lastXP, lastMax = cur, max
  updateTracker()
end

-- 2. Pre-pull check -----------------------------------------------------------
local hud, hudIcons, hudText = nil, {}, nil
local CHECK_BUFFS = { "Mark of the Wild", "Thorns", "Rejuvenation" }

local function nearbyEnemies()
  if not (C_NamePlate and C_NamePlate.GetNamePlates) then return nil end
  local n = 0
  for _, plate in ipairs(safe(C_NamePlate.GetNamePlates) or {}) do
    local unit = plate.namePlateUnitToken or (plate.UnitFrame and plate.UnitFrame.unit)
    if unit and UnitCanAttack("player", unit) and not UnitIsDead(unit) and not UnitIsPlayer(unit) then n = n + 1 end
  end
  return n
end

local function updateHud()
  if not hud then return end
  if not DB.hudOn or InCombatLockdown() or UnitIsDeadOrGhost("player") then hud:Hide(); return end
  local ready, shown = true, 0
  for i, name in ipairs(CHECK_BUFFS) do
    local ic = hudIcons[i]
    if known(name) then
      shown = shown + 1
      ic:Show()
      ic.tex:SetTexture(spellIcon(name) or "Interface\\Icons\\INV_Misc_QuestionMark")
      local on = hasBuff(name)
      ic.tex:SetDesaturated(not on)
      ic.tex:SetAlpha(on and 1 or 0.45)
      ic.mark:SetText(on and "" or RED .. "!|r")
      if not on then ready = false end
    else
      ic:Hide()
    end
  end
  local hp, mp = healthPct(), manaPct()
  fillBar(hud.hpBar, UnitHealth("player"), UnitHealthMax("player"))
  fillBar(hud.mpBar, UnitPower("player", 0), UnitPowerMax("player", 0))
  if (hp and hp < 80) or (mp and mp < 70) then ready = false end
  local enemies = nearbyEnemies()
  local parts = {}
  if hp then table.insert(parts, (hp >= 80 and LEAF or RED) .. "HP " .. hp .. "%|r") end
  if mp then table.insert(parts, (mp >= 70 and LEAF or RED) .. "MP " .. mp .. "%|r") end
  if enemies then
    table.insert(parts, (enemies >= 3 and RED or (enemies == 2 and DRUID or LEAF)) .. enemies .. " near|r")
  end
  -- Forever: cooked food's Well Fed buff gives +5% XP from kills (15 min). Word, not colour, says it.
  if UnitLevel("player") < (GetMaxPlayerLevel and GetMaxPlayerLevel() or 60) then
    table.insert(parts, hasBuff("Well Fed") and (LEAF .. "FED|r") or (RED .. "EAT: +5% XP|r"))
  end
  hudText:SetText(table.concat(parts, "  ") .. "   " .. (ready and LEAF .. "READY|r" or GREY .. "not ready|r"))
  hud:Show()
end

-- 3. Level-up assistant --------------------------------------------------------
local TRAIN = {
  [14] = "Bash (stun in Bear Form); start Power over Poison for Cure Poison",
  [16] = "Aquatic Form class quest",
  [18] = "Faerie Fire and Hibernate",
  [20] = "Cat Form class quest (Darnassus trainer). Talent points: Feral list on the Talents tab (Alt+7)",
  [30] = "Travel Form and Tranquility",
  [40] = "Dire Bear Form, Innervate, dual spec, first mount",
  [44] = "Barkskin",
}
local function greyCutoff(lvl)
  if lvl <= 5 then return 0 end
  return lvl - math.floor(lvl / 10) - 5
end
local function greyQuestCount(lvl)
  local cut, n = greyCutoff(lvl), 0
  if C_QuestLog and C_QuestLog.GetNumQuestLogEntries and C_QuestLog.GetInfo then
    for i = 1, (safe(C_QuestLog.GetNumQuestLogEntries) or 0) do
      local q = safe(C_QuestLog.GetInfo, i)
      if q and not q.isHeader and q.level and q.level > 0 and q.level <= cut then n = n + 1 end
    end
  elseif GetNumQuestLogEntries then
    for i = 1, (safe(GetNumQuestLogEntries) or 0) do
      local _, ql, _, header = safe(GetQuestLogTitle, i)
      if not header and ql and ql > 0 and ql <= cut then n = n + 1 end
    end
  end
  return n
end
local function onLevelUp(newLevel)
  shout(("Level %d!"):format(newLevel))
  say(DRUID .. ("Level %d.|r"):format(newLevel))
  if newLevel >= 10 then say("You have a talent point to spend (N). Combat Guide has the order.") end
  if newLevel % 2 == 0 then
    say("New spells and ranks at your trainer: Teleport: Moonglade. Then /dk bars." .. (TRAIN[newLevel] and (" New: " .. TRAIN[newLevel] .. ".") or ""))
  elseif TRAIN[newLevel] then
    say("Unlocked: " .. TRAIN[newLevel] .. ".")
  end
  C_Timer.After(2, function()
    local g = greyQuestCount(newLevel)
    if g > 0 then say(("%d quest%s in your log %s now grey (little XP). Consider abandoning."):format(g, g == 1 and "" or "s", g == 1 and "is" or "are")) end
  end)
end

local warned = {}
local function checkDurability()
  local low
  for slot = 1, 18 do
    local cur, max = safe(GetInventoryItemDurability, slot)
    if cur and max and max > 0 then
      local p = cur / max * 100
      if not low or p < low then low = p end
    end
  end
  if low and low < 50 then
    if not warned.dura then
      warned.dura = true
      shout(low <= 0 and "Gear BROKEN: repair now!" or "Gear below 50%: repair in town", 1, 0.3, 0.3)
    end
  else
    warned.dura = nil
  end
end
local function freeBagSlots()
  local free = 0
  for bag = 0, 4 do
    free = free + ((C_Container and C_Container.GetContainerNumFreeSlots and safe(C_Container.GetContainerNumFreeSlots, bag))
      or (GetContainerNumFreeSlots and safe(GetContainerNumFreeSlots, bag)) or 0)
  end
  return free
end
local lastBagWarn = 0
local function checkBags()
  local free = freeBagSlots()
  if free <= 2 and GetTime() - lastBagWarn > 300 then
    lastBagWarn = GetTime()
    shout(free == 0 and "Bags full!" or ("Bags nearly full (%d free)"):format(free), 1, 0.82, 0)
  end
end

-- 4. Rest prompt ---------------------------------------------------------------
local rest, restText
local resting, readyUntil = false, 0
local function eatingOrDrinking() return hasBuff("Food") or hasBuff("Drink") or hasBuff("Food & Drink") end
local function updateRest()
  if not rest then return end
  if not DB.restOn or InCombatLockdown() or UnitIsDeadOrGhost("player") then rest:Hide(); return end
  local hp, mp = healthPct(), manaPct()
  if not hp or not mp then
    -- Exact numbers hidden: just show the bars while you eat or drink.
    if eatingOrDrinking() then
      restText:SetText(LEAF .. "Resting|r")
      fillBar(rest.hpBar, UnitHealth("player"), UnitHealthMax("player"))
      fillBar(rest.mpBar, UnitPower("player", 0), UnitPowerMax("player", 0))
      rest.hpBar:Show(); rest.mpBar:Show()
      rest:Show()
    else
      rest:Hide()
    end
    return
  end
  rest.hpBar:Hide(); rest.mpBar:Hide()
  if hp < 70 or mp < 50 then resting = true end
  if resting then
    if hp >= 95 and mp >= 90 then
      resting = false
      readyUntil = GetTime() + 2.5
    else
      local doing = eatingOrDrinking()
      restText:SetText((doing and LEAF .. "Resting|r" or DRUID .. "Eat & drink|r") .. ("   " .. GREY .. "HP %d%%  MP %d%%|r"):format(hp, mp))
      rest:Show()
      return
    end
  end
  if GetTime() < readyUntil then
    restText:SetText(LEAF .. "Ready|r")
    rest:Show()
  else
    rest:Hide()
  end
end

-- Build UI and wire events -----------------------------------------------------
local function build()
  tracker = makePanel("tracker", 280, 54, "TOPRIGHT", -210, -200)
  trackerText = tracker:CreateFontString(nil, "OVERLAY", "GameFontHighlightSmall")
  trackerText:SetPoint("TOPLEFT", 8, -7); trackerText:SetWidth(264); trackerText:SetJustifyH("LEFT")
  trackerText:SetSpacing(2)

  hud = makePanel("hud", 380, 34, "CENTER", 0, -190)
  for i = 1, #CHECK_BUFFS do
    local ic = CreateFrame("Frame", nil, hud)
    ic:SetSize(22, 22)
    ic:SetPoint("LEFT", hud, "LEFT", 6 + (i - 1) * 25, 0)
    ic.tex = ic:CreateTexture(nil, "ARTWORK"); ic.tex:SetAllPoints()
    ic.mark = ic:CreateFontString(nil, "OVERLAY", "GameFontNormal"); ic.mark:SetPoint("BOTTOMRIGHT", 2, -2)
    hudIcons[i] = ic
  end
  local function bar(parent, r, g, b, w)
    local sb = CreateFrame("StatusBar", nil, parent)
    sb:SetSize(w, 6)
    sb:SetStatusBarTexture("Interface\\TargetingFrame\\UI-StatusBar")
    sb:SetStatusBarColor(r, g, b)
    local bg = sb:CreateTexture(nil, "BACKGROUND"); bg:SetAllPoints(); bg:SetColorTexture(0, 0, 0, 0.6)
    return sb
  end
  local left = 6 + #CHECK_BUFFS * 25 + 4
  hud.hpBar = bar(hud, 0.2, 0.85, 0.2, 60); hud.hpBar:SetPoint("LEFT", hud, "LEFT", left, 4)
  hud.mpBar = bar(hud, 0.25, 0.45, 1, 60);  hud.mpBar:SetPoint("LEFT", hud, "LEFT", left, -4)
  hudText = hud:CreateFontString(nil, "OVERLAY", "GameFontHighlightSmall")
  hudText:SetPoint("LEFT", hud, "LEFT", left + 66, 0)

  rest = makePanel("rest", 220, 40, "CENTER", 0, 140)
  restText = rest:CreateFontString(nil, "OVERLAY", "GameFontNormalLarge")
  restText:SetPoint("TOP", 0, -6)
  rest.hpBar = bar(rest, 0.2, 0.85, 0.2, 180); rest.hpBar:SetPoint("BOTTOM", 0, 13)
  rest.mpBar = bar(rest, 0.25, 0.45, 1, 180);  rest.mpBar:SetPoint("BOTTOM", 0, 5)
  rest.hpBar:Hide(); rest.mpBar:Hide()
  for _, f in pairs(panels) do f:EnableMouse(false); f:Hide() end
end

local ev = CreateFrame("Frame")
for _, e in ipairs({ "PLAYER_LOGIN", "PLAYER_XP_UPDATE", "PLAYER_LEVEL_UP", "PLAYER_REGEN_ENABLED", "PLAYER_REGEN_DISABLED",
                     "UNIT_AURA", "UPDATE_INVENTORY_DURABILITY", "BAG_UPDATE_DELAYED", "FRIENDLIST_UPDATE",
                     "BN_FRIEND_INFO_CHANGED", "GUILD_ROSTER_UPDATE", "NAME_PLATE_UNIT_ADDED", "NAME_PLATE_UNIT_REMOVED", "SKILL_LINES_CHANGED", "PLAYER_MONEY" }) do
  pcall(ev.RegisterEvent, ev, e)
end
local errors = 0
local function guard(fn, ...)
  if errors >= 5 then return end
  local ok, err = pcall(fn, ...)
  if not ok then
    errors = errors + 1
    if errors == 5 then
      say("helper panels hit repeated errors and paused themselves until /reload. Tell Claude: " .. tostring(err))
    end
  end
end
local function onEvent(_, e, a1)
  if e == "PLAYER_LOGIN" then
    DruidKitDB = DruidKitDB or {}
    DB = DruidKitDB
    opt("trackerOn", true); opt("hudOn", true); opt("restOn", true)
    DB.sessionStart = GetTime()
    build()
    lastXP, lastMax = UnitXP("player"), UnitXPMax("player")
    if C_FriendList and C_FriendList.ShowFriends then pcall(C_FriendList.ShowFriends) end
    friendLevels()
    updateTracker(); updateHud(); updateRest()
    return
  end
  if not DB then return end
  if e == "PLAYER_XP_UPDATE" then onXP()
  elseif e == "PLAYER_LEVEL_UP" then onLevelUp(a1); C_Timer.After(1, updateTracker)
  elseif e == "PLAYER_REGEN_DISABLED" then hud:Hide(); rest:Hide()
  elseif e == "PLAYER_REGEN_ENABLED" then C_Timer.After(0.3, function() updateHud(); updateRest() end)
  elseif e == "UNIT_AURA" and a1 == "player" then updateHud(); updateRest()
  elseif e == "UPDATE_INVENTORY_DURABILITY" then checkDurability()
  elseif e == "BAG_UPDATE_DELAYED" then checkBags()
  elseif e == "SKILL_LINES_CHANGED" or e == "PLAYER_MONEY" then updateTracker()
  elseif e == "FRIENDLIST_UPDATE" or e == "BN_FRIEND_INFO_CHANGED" or e == "GUILD_ROSTER_UPDATE" then friendLevels(); updateTracker()
  elseif e == "NAME_PLATE_UNIT_ADDED" or e == "NAME_PLATE_UNIT_REMOVED" then updateHud()
  end
end
ev:SetScript("OnEvent", function(...) guard(onEvent, ...) end)

-- light polling for health/mana changes while out of combat
local acc = 0
ev:SetScript("OnUpdate", function(_, elapsed)
  if not DB then return end
  acc = acc + elapsed
  if acc < 0.5 then return end
  acc = 0
  if not InCombatLockdown() then guard(updateHud); guard(updateRest) end
end)
C_Timer.NewTicker(30, function() if DB then guard(updateTracker) end end)

-- Extra /dk commands (DruidKit.lua passes unknown commands here)
function DruidKit_HelperCommand(cmd, arg)
  if not DB then return false end
  local on
  if arg == "on" then on = true elseif arg == "off" then on = false end
  if cmd == "catchup" then
    local n = tonumber(arg)
    if n then
      DB.catchupTarget = n; DB.catchupFriend = nil
      say("catching up to level " .. n .. ".")
    elseif arg and arg ~= "" then
      DB.catchupFriend = arg:lower()
      local lvl, name = findFriend(DB.catchupFriend)
      say(lvl and ("catching up to %s (level %d)."):format(name, lvl) or ("tracking %s: add him as a friend so his level shows."):format(arg))
    else
      DB.catchupTarget = nil; DB.catchupFriend = nil
      say("catching up to your highest friend.")
    end
    updateTracker()
  elseif cmd == "tracker" and on ~= nil then DB.trackerOn = on; if on then updateTracker() else tracker:Hide() end
  elseif cmd == "hud" and on ~= nil then DB.hudOn = on; updateHud()
  elseif cmd == "rest" and on ~= nil then DB.restOn = on; updateRest()
  elseif cmd == "trainers" and DruidKit_TrainersCommand then DruidKit_TrainersCommand(arg)
  elseif cmd == "bags" and DruidKit_ToggleBags then DruidKit_ToggleBags()
  elseif (cmd == "go" or cmd == "goto") and DruidKit_ToggleGo then DruidKit_ToggleGo()
  elseif cmd == "party" and DruidKit_PartyCommand then DruidKit_PartyCommand(arg)
  elseif cmd == "unlock" then setUnlocked(true); if DruidKit_PartyMovable then DruidKit_PartyMovable(true) end
  elseif cmd == "lock" then setUnlocked(false); if DruidKit_PartyMovable then DruidKit_PartyMovable(false) end; updateHud(); updateRest(); updateTracker()
  else return false end
  return true
end
