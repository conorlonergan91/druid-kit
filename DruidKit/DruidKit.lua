-- Druid Kit
--   /dk bars          lay out action bars and keys to match the Combat Guide (known spells only)
--   /dk save NAME     save your current bars as a named layout
--   /dk load NAME     load a saved layout ("/dk load backup" undoes the last /dk bars)
--   /dk list          list saved layouts
--   /dk herbs         turn Find Herbs back on (or show the one-click button)
-- Bars and keys can only change out of combat; the addon waits for combat to end if needed.

local PREFIX = "|cff7fd35bDruid Kit:|r "
local function say(msg) print(PREFIX .. msg) end
local function safe(fn, ...)
  if not fn then return nil end
  local ok, a, b, c, d, e, f = pcall(fn, ...)
  if ok then return a, b, c, d, e, f end
end

-- ---------------------------------------------------------------------------
-- Layout from the Combat Guide. Slots: 1-12 main bar (caster), 97-108 Bear Form bar,
-- 61-72 bottom-left bar, 49-60 bottom-right bar.
-- ---------------------------------------------------------------------------
-- Keys ordered by how easy they are to reach: 3 easiest, then 2 and 4, then 1 and 5; 6+ for rare things.
-- melee = true: placed as a small macro that also starts auto attack (/startattack), so it never stops.
local LAYOUT = {
  -- caster bar, keys 1-9
  { slot = 3,   spell = "Moonfire" },            -- pull
  { slot = 2,   spell = "Wrath" },
  { slot = 4,   spell = "Regrowth" },            -- heal between fights
  { slot = 1,   spell = "Rejuvenation" },
  { slot = 5,   spell = "Healing Touch" },
  { slot = 6,   spell = "Entangling Roots" },
  { slot = 7,   spell = "Faerie Fire" },
  { slot = 8,   spell = "Hibernate" },
  { slot = 9,   spell = "Cure Poison" },
  -- Bear Form bar, keys 1-8
  { slot = 99,  spell = "Maul", melee = true },  -- key 3
  { slot = 98,  spell = "Swipe", melee = true }, -- key 2
  { slot = 100, spell = "Lacerate", melee = true },
  { slot = 97,  spell = "Enrage" },
  { slot = 101, spell = "Demoralizing Roar" },
  { slot = 102, spell = "Bash", melee = true },
  { slot = 103, spell = "Growl" },
  { slot = 104, spell = "Faerie Fire (Feral)" },
  -- Cat Form bar (from level 20), keys 1-9
  { slot = 75,  spell = "Claw", melee = true },  -- key 3
  { slot = 74,  spell = "Rake", melee = true },
  { slot = 76,  spell = "Rip", melee = true },
  { slot = 73,  spell = "Tiger's Fury" },
  { slot = 77,  spell = "Ferocious Bite", melee = true },
  { slot = 78,  spell = "Shred", melee = true },
  { slot = 79,  spell = "Prowl" },
  { slot = 80,  spell = "Dash" },
  { slot = 81,  spell = "Faerie Fire (Feral)" },
  -- Prowling (stealth openers): plain spells, so auto attack doesn't break stealth early
  { slot = 87,  spell = "Ravage" },              -- key 3
  { slot = 86,  spell = "Pounce" },
  { slot = 88,  spell = "Shred" },
  { slot = 85,  spell = "Tiger's Fury" },
  -- bottom-left bar: R, then Shift+1..8
  { slot = 61,  spell = "Attack" },
  { slot = 63,  spell = "Mark of the Wild" },
  { slot = 64,  spell = "Thorns" },
  { slot = 66,  item = 6948 },               -- Hearthstone
  { slot = 67,  spell = "Find Herbs" },
  { slot = 69,  spell = "Revive" },
  { slot = 70,  spell = "Teleport: Moonglade" },
  -- bottom-right bar: Shift+F
  { slot = 49,  spell = "Nature's Grasp" },
}
-- Slots 65 (Shift+3, food) and 68 (Shift+6, potion) are left for you: drag food and potions there.

-- Healing preset: only the caster bar (keys 1 to =) changes. Bear bar and Shift keys stay the same.
local LAYOUT_HEAL = {
  { slot = 3,  spell = "Rejuvenation" },
  { slot = 2,  spell = "Regrowth" },
  { slot = 4,  spell = "Healing Touch" },
  { slot = 1,  spell = "Swiftmend" },
  { slot = 5,  spell = "Wild Growth" },
  { slot = 6,  spell = "Cure Poison" },
  { slot = 7,  spell = "Remove Curse" },
  { slot = 8,  spell = "Nature's Swiftness" },
  { slot = 9,  spell = "Rebirth" },
  { slot = 10, spell = "Innervate" },
  { slot = 11, spell = "Tranquility" },
  { slot = 12, spell = "Moonfire" },
}
local function layoutFor(mode)
  if mode ~= "heal" then return LAYOUT end
  local t = {}
  for _, e in ipairs(LAYOUT) do if e.slot > 12 then table.insert(t, e) end end
  for _, e in ipairs(LAYOUT_HEAL) do table.insert(t, e) end
  return t
end
local function currentLayout() return layoutFor(DruidKitDB and DruidKitDB.barMode) end
local ALL_LAYOUT_SPELLS = {}
for _, e in ipairs(LAYOUT) do if e.spell then ALL_LAYOUT_SPELLS[e.spell] = true end end
for _, e in ipairs(LAYOUT_HEAL) do ALL_LAYOUT_SPELLS[e.spell] = true end

local BINDINGS = {
  { key = "R",       action = "MULTIACTIONBAR1BUTTON1" },
  { key = "SHIFT-1", action = "MULTIACTIONBAR1BUTTON3" },
  { key = "SHIFT-2", action = "MULTIACTIONBAR1BUTTON4" },
  { key = "SHIFT-3", action = "MULTIACTIONBAR1BUTTON5" },
  { key = "SHIFT-4", action = "MULTIACTIONBAR1BUTTON6" },
  { key = "SHIFT-5", action = "MULTIACTIONBAR1BUTTON7" },
  { key = "SHIFT-6", action = "MULTIACTIONBAR1BUTTON8" },
  { key = "SHIFT-7", action = "MULTIACTIONBAR1BUTTON9" },
  { key = "SHIFT-8", action = "MULTIACTIONBAR1BUTTON10" },
  { key = "SHIFT-F", action = "MULTIACTIONBAR2BUTTON1" },
  { key = "F",       action = "SHAPESHIFTBUTTON1" },   -- Bear Form
  { key = "G",       action = "SHAPESHIFTBUTTON3" },   -- Cat Form, once learned at 20
}

-- ---------------------------------------------------------------------------
-- Game API wrappers (Forever uses a mix of old and new names)
-- ---------------------------------------------------------------------------
local function spellIDByName(name)
  if C_Spell and C_Spell.GetSpellInfo then
    local info = safe(C_Spell.GetSpellInfo, name)
    if type(info) == "table" and info.spellID then return info.spellID end
  end
  if GetSpellInfo then
    local _, _, _, _, _, _, id = safe(GetSpellInfo, name)
    return id
  end
end

local function isKnown(name)
  if name == "Attack" then return true end
  local id = spellIDByName(name)
  if not id then return false end
  if C_SpellBook and C_SpellBook.IsSpellKnown then return safe(C_SpellBook.IsSpellKnown, id) and true or false end
  if IsPlayerSpell then return safe(IsPlayerSpell, id) and true or false end
  if IsSpellKnown then return safe(IsSpellKnown, id) and true or false end
  return true
end

local function pickupSpell(name)
  local id = (name == "Attack") and 6603 or spellIDByName(name)
  if not id then return false end
  if C_Spell and C_Spell.PickupSpell then safe(C_Spell.PickupSpell, id)
  elseif PickupSpell then safe(PickupSpell, id) end
  return (GetCursorInfo and GetCursorInfo()) ~= nil
end

-- A tiny per-character macro: "/startattack" then the spell, so auto attack always stays on.
local function meleeMacro(spell)
  if not (CreateMacro and GetMacroIndexByName) then return end
  local name = ("DK %s"):format(spell):sub(1, 16)
  local body = ("#showtooltip %s\n/startattack\n/cast %s"):format(spell, spell)
  local idx = safe(GetMacroIndexByName, name) or 0
  if idx == 0 then
    idx = safe(CreateMacro, name, "INV_MISC_QUESTIONMARK", body, true) or 0
  elseif EditMacro then
    safe(EditMacro, idx, name, "INV_MISC_QUESTIONMARK", body)
  end
  return idx ~= 0 and idx or nil
end
local function pickupEntry(e)
  if e.melee then
    local idx = meleeMacro(e.spell)
    if idx and PickupMacro then
      safe(PickupMacro, idx)
      if (GetCursorInfo and GetCursorInfo()) ~= nil then return true end
    end
  end
  return pickupSpell(e.spell)   -- no room for a macro: plain spell
end

local function pickupItem(id)
  if C_Item and C_Item.PickupItem then safe(C_Item.PickupItem, id) elseif PickupItem then safe(PickupItem, id) end
  return (GetCursorInfo and GetCursorInfo()) ~= nil
end

local function hasAction(slot)
  if C_ActionBar and C_ActionBar.HasAction then return safe(C_ActionBar.HasAction, slot) end
  return safe(HasAction, slot)
end

local function getActionInfo(slot)
  if C_ActionBar and C_ActionBar.GetActionInfo then return safe(C_ActionBar.GetActionInfo, slot) end
  return safe(GetActionInfo, slot)
end

local function place(slot)
  if C_ActionBar and C_ActionBar.PlaceAction then safe(C_ActionBar.PlaceAction, slot)
  elseif PlaceAction then safe(PlaceAction, slot) end
  ClearCursor()
end

local function clearSlot(slot)
  if hasAction(slot) then
    if C_ActionBar and C_ActionBar.PickupAction then safe(C_ActionBar.PickupAction, slot)
    elseif PickupAction then safe(PickupAction, slot) end
    ClearCursor()
  end
end

-- ---------------------------------------------------------------------------
-- Save / load layouts
-- ---------------------------------------------------------------------------
local SLOTS = {}
for _, r in ipairs({ { 1, 12 }, { 49, 72 }, { 73, 96 }, { 97, 108 } }) do
  for s = r[1], r[2] do table.insert(SLOTS, s) end
end

local function captureBars()
  local layout = {}
  for _, slot in ipairs(SLOTS) do
    local kind, id = getActionInfo(slot)
    if kind then layout[slot] = { kind = kind, id = id } end
  end
  return layout
end

local function restoreBars(layout)
  local placed = 0
  for _, slot in ipairs(SLOTS) do
    local a = layout[slot]
    if a then
      local ok = false
      if a.kind == "spell" then
        if C_Spell and C_Spell.PickupSpell then safe(C_Spell.PickupSpell, a.id) elseif PickupSpell then safe(PickupSpell, a.id) end
        ok = GetCursorInfo() ~= nil
      elseif a.kind == "item" then
        ok = pickupItem(a.id)
      elseif a.kind == "macro" then
        safe(PickupMacro, a.id); ok = GetCursorInfo() ~= nil
      end
      if ok then place(slot); placed = placed + 1 else ClearCursor() end
    else
      clearSlot(slot)
    end
  end
  return placed
end

-- ---------------------------------------------------------------------------
-- Run things out of combat only
-- ---------------------------------------------------------------------------
local pending
local function outOfCombat(fn, label)
  if InCombatLockdown() then
    pending = fn
    say(label .. " will run when combat ends.")
  else
    fn()
  end
end

-- Changing action bars (or key bindings) from addon code "taints" Blizzard's action bars for the
-- rest of the session: in combat they can vanish, and bear form stops swapping keys.
-- A /reload clears it, so after any bar or key change we offer one. Nothing reloads by itself.
StaticPopupDialogs["DRUIDKIT_RELOAD"] = {
  text = "Druid Kit changed your action bars.\n\nReload now so they keep working in combat and in bear form?",
  button1 = "Reload now", button2 = "Later",
  OnAccept = function() ReloadUI() end,
  timeout = 0, whileDead = true, hideOnEscape = true, preferredIndex = 3,
}
local reloadPending = false
local function askReload()
  if InCombatLockdown() then reloadPending = true; return end
  reloadPending = false
  StaticPopup_Show("DRUIDKIT_RELOAD")
  say("bars changed: click Reload now (or type /reload) before your next fight.")
end
DruidKit_AskReload = askReload

local knownLayoutSpells
local function knownLayoutSpellAt(slot)
  for _, e in ipairs(currentLayout()) do
    if e.slot == slot and ((e.spell and isKnown(e.spell)) or e.item) then return true end
  end
  return false
end
local function applyGuideLayout()
  DruidKitDB.layouts = DruidKitDB.layouts or {}
  DruidKitDB.layouts.backup = captureBars()
  local placed, skipped = 0, {}
  for _, e in ipairs(currentLayout()) do
    if e.item then
      if (GetItemCount and safe(GetItemCount, e.item) or 0) > 0 or (C_Item and C_Item.GetItemCount and safe(C_Item.GetItemCount, e.item) or 0) > 0 then
        if pickupItem(e.item) then place(e.slot); placed = placed + 1 end
      end
    elseif isKnown(e.spell) then
      if pickupEntry(e) then place(e.slot); placed = placed + 1 else ClearCursor() end
    else
      -- Not learned yet: empty the button so nothing old or doubled sits there.
      -- It fills in by itself when you train the skill.
      if not knownLayoutSpellAt(e.slot) then clearSlot(e.slot) end
      local seen = false
      for _, n in ipairs(skipped) do if n == e.spell then seen = true end end
      if not seen then table.insert(skipped, e.spell) end
    end
  end
  for _, b in ipairs(BINDINGS) do safe(SetBinding, b.key, b.action) end
  local set = GetCurrentBindingSet and GetCurrentBindingSet() or 1
  safe(SaveBindings, set)
  say(("bars set: %d placed, keys bound. Empty until you learn them: %s."):format(placed, #skipped > 0 and table.concat(skipped, ", ") or "none"))
  local caster, bear, cat = {}, {}, {}
  for _, e in ipairs(currentLayout()) do
    local name = e.spell or "Hearthstone"
    local ok = e.item or isKnown(e.spell)
    if e.slot <= 12 then table.insert(caster, e.slot .. " " .. (ok and name or "-")) end
    if e.slot >= 97 and e.slot <= 108 then table.insert(bear, (e.slot - 96) .. " " .. (ok and name or "-")) end
    if e.slot >= 73 and e.slot <= 84 and ok then table.insert(cat, (e.slot - 72) .. " " .. name) end
  end
  local byNum = function(a, b) return (tonumber(a:match("^%d+")) or 0) < (tonumber(b:match("^%d+")) or 0) end
  table.sort(caster, byNum); table.sort(bear, byNum); table.sort(cat, byNum)
  if #cat > 0 then say("Cat keys: " .. table.concat(cat, " \194\183 ")) end
  say("Caster keys: " .. table.concat(caster, " \194\183 "))
  say("Bear keys: " .. table.concat(bear, " \194\183 "))
  say("Your old bars are saved: type /dk load backup to undo.")
  DruidKitDB.knownSpells = knownLayoutSpells()
  askReload()
end

-- ---------------------------------------------------------------------------
-- New skills go straight onto your bars when you learn them
-- ---------------------------------------------------------------------------
local function slotKey(slot)
  if slot >= 1 and slot <= 12 then return "key " .. slot end
  if slot >= 97 and slot <= 108 then return "bear key " .. (slot - 96) end
  if slot >= 73 and slot <= 84 then return "cat key " .. (slot - 72) end
  if slot >= 85 and slot <= 96 then return "prowl key " .. (slot - 84) end
  if slot == 61 then return "R" end
  if slot >= 63 and slot <= 70 then return "Shift+" .. (slot - 62) end
  if slot == 49 then return "Shift+F" end
  return "slot " .. slot
end

knownLayoutSpells = function()
  local set = {}
  for name in pairs(ALL_LAYOUT_SPELLS) do if isKnown(name) then set[name] = true end end
  return set
end

local function addNewSpells()
  if InCombatLockdown() then pending = addNewSpells; return end
  if GetShapeshiftForm and GetShapeshiftForm() ~= 0 then return end  -- spell lists change in forms; only check in caster form
  local now = knownLayoutSpells()
  local before = DruidKitDB.knownSpells
  DruidKitDB.knownSpells = now
  if not before then return end              -- first run: just remember what you know
  local added = {}
  for _, e in ipairs(currentLayout()) do
    if e.spell and now[e.spell] and not before[e.spell] then
      if #added == 0 then DruidKitDB.layouts = DruidKitDB.layouts or {}; DruidKitDB.layouts.backup = captureBars() end
      if pickupEntry(e) then place(e.slot); table.insert(added, e.spell .. " (" .. slotKey(e.slot) .. ")") else ClearCursor() end
    end
  end
  if #added > 0 then
    say("new skill on your bars: " .. table.concat(added, ", ") .. ". /dk load backup to undo.")
    askReload()
  end
end

-- ---------------------------------------------------------------------------
-- Healing mode / questing mode: bars and gear swap together
--   /dk heal  /dk quest  (or Alt+H to toggle)   /dk healset  /dk questset
-- ---------------------------------------------------------------------------
local GEAR_SLOTS = { 1, 2, 3, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18 }

local function saveGearSet(mode)
  DruidKitDB.gearSets = DruidKitDB.gearSets or {}
  local set, n = {}, 0
  for _, slot in ipairs(GEAR_SLOTS) do
    local link = GetInventoryItemLink("player", slot)
    if link then set[slot] = link; n = n + 1 end
  end
  DruidKitDB.gearSets[mode] = set
  say(("saved %d pieces as your %s set. Bag check will keep them, and Bank check offers to store them when you're in the other mode."):format(n, mode == "heal" and "healing" or "questing"))
end

local function wearGearSet(mode)
  local set = DruidKitDB.gearSets and DruidKitDB.gearSets[mode]
  if not set then return 0, true end
  local missing = 0
  for slot, link in pairs(set) do
    local worn = GetInventoryItemLink("player", slot)
    local wantID, wornID = link:match("item:(%d+)"), worn and worn:match("item:(%d+)")
    if wantID ~= wornID then
      local have = (C_Item and C_Item.GetItemCount and safe(C_Item.GetItemCount, link)) or (GetItemCount and safe(GetItemCount, link)) or 0
      if have > 0 then
        if C_Item and C_Item.EquipItemByName then safe(C_Item.EquipItemByName, link, slot) else safe(EquipItemByName, link, slot) end
      else
        missing = missing + 1
      end
    end
  end
  return missing, false
end

local function fillLearned(layout)
  local n = 0
  for _, e in ipairs(layout) do
    if e.spell and not hasAction(e.slot) and isKnown(e.spell) then
      if pickupSpell(e.spell) then place(e.slot); n = n + 1 else ClearCursor() end
    end
  end
  return n
end

local function switchMode(mode)
  if InCombatLockdown() then pending = function() switchMode(mode) end; say("switching after combat."); return end
  DruidKitDB.layouts = DruidKitDB.layouts or {}
  local cur = DruidKitDB.barMode or "quest"
  if cur == mode then
    -- already in this mode: just re-wear the set and fill any newly learned spells
  else
    DruidKitDB.layouts["mode_" .. cur] = captureBars()
  end
  DruidKitDB.barMode = mode
  local snap = DruidKitDB.layouts["mode_" .. mode]
  if cur ~= mode and snap then
    restoreBars(snap)
    fillLearned(layoutFor(mode))
  elseif cur ~= mode then
    applyGuideLayout()
  end
  DruidKitDB.knownSpells = knownLayoutSpells()
  local missing, noSet = wearGearSet(mode)
  local label = mode == "heal" and "Healing mode" or "Questing mode"
  local gear = noSet and ("no " .. (mode == "heal" and "healing" or "questing") .. " set saved yet (/dk " .. mode .. "set)")
    or (missing > 0 and (missing .. " set piece(s) not in your bags: check the bank") or "gear swapped")
  say(label .. ": bars switched, " .. gear .. ".")
  askReload()
  if DruidKitBagsAPI and DruidKitBagsAPI.refresh then pcall(DruidKitBagsAPI.refresh) end
end

function DruidKit_ToggleMode()
  switchMode((DruidKitDB.barMode == "heal") and "quest" or "heal")
end
BINDING_NAME_DRUIDKIT_TOGGLEMODE = "Switch healing / questing mode"

-- ---------------------------------------------------------------------------
-- Find Herbs after death
-- ---------------------------------------------------------------------------
local function findHerbsTrackingIndex()
  if not (C_Minimap and C_Minimap.GetNumTrackingTypes) then return nil end
  local n = safe(C_Minimap.GetNumTrackingTypes) or 0
  for i = 1, n do
    local a, _, active = safe(C_Minimap.GetTrackingInfo, i)
    local name = type(a) == "table" and a.name or a
    if type(a) == "table" then active = a.active end
    if name == "Find Herbs" then return i, active end
  end
end

local herbButton = CreateFrame("Button", "DruidKitHerbButton", UIParent, "SecureActionButtonTemplate,UIPanelButtonTemplate")
herbButton:SetSize(260, 44)
herbButton:SetPoint("CENTER", UIParent, "CENTER", 0, 160)
herbButton:SetText("Click to turn on Find Herbs")
herbButton:SetAttribute("type", "spell")
herbButton:SetAttribute("spell", "Find Herbs")
herbButton:RegisterForClicks("AnyUp", "AnyDown")
herbButton:Hide()
herbButton:HookScript("OnClick", function(self)
  C_Timer.After(0.5, function() if not InCombatLockdown() then self:Hide() end end)
end)

local function herbsOn()
  if not isKnown("Find Herbs") then return end
  local idx, active = findHerbsTrackingIndex()
  if active then herbButton:Hide(); return end
  if idx and C_Minimap.SetTracking then safe(C_Minimap.SetTracking, idx, true) end
  C_Timer.After(1, function()
    local _, nowActive = findHerbsTrackingIndex()
    if nowActive then
      herbButton:Hide()
      say("Find Herbs is back on.")
    elseif not InCombatLockdown() then
      herbButton:Show()
    end
  end)
end

-- ---------------------------------------------------------------------------
-- Events and slash command
-- ---------------------------------------------------------------------------
local ev = CreateFrame("Frame")
ev:RegisterEvent("ADDON_LOADED")
ev:RegisterEvent("PLAYER_UNGHOST")
ev:RegisterEvent("PLAYER_ALIVE")
ev:RegisterEvent("PLAYER_ENTERING_WORLD")
ev:RegisterEvent("PLAYER_REGEN_ENABLED")
pcall(ev.RegisterEvent, ev, "LEARNED_SPELL_IN_TAB")
pcall(ev.RegisterEvent, ev, "LEARNED_SPELL_IN_SKILL_LINE")
local spellCheckQueued = false
local function queueSpellCheck()
  if spellCheckQueued then return end
  spellCheckQueued = true
  C_Timer.After(1.5, function() spellCheckQueued = false; pcall(addNewSpells) end)
end
ev:SetScript("OnEvent", function(_, event, arg1)
  if event == "ADDON_LOADED" and arg1 == "DruidKit" then
    DruidKitDB = DruidKitDB or {}
    DruidKitDB.layouts = DruidKitDB.layouts or {}
  elseif event == "PLAYER_REGEN_ENABLED" then
    if pending then local fn = pending; pending = nil; fn() end
    if reloadPending then askReload() end
  elseif event == "LEARNED_SPELL_IN_TAB" or event == "LEARNED_SPELL_IN_SKILL_LINE" then
    if DruidKitDB then queueSpellCheck() end
  elseif event == "PLAYER_UNGHOST" or event == "PLAYER_ALIVE" or event == "PLAYER_ENTERING_WORLD" then
    if not UnitIsDeadOrGhost("player") then C_Timer.After(2, herbsOn) end
    if event == "PLAYER_ENTERING_WORLD" and DruidKitDB and not DruidKitDB.knownSpells then
      C_Timer.After(3, function() if GetShapeshiftForm and GetShapeshiftForm() == 0 then DruidKitDB.knownSpells = knownLayoutSpells() end end)
    end
  end
end)

SLASH_DRUIDKIT1 = "/dk"
SlashCmdList["DRUIDKIT"] = function(msg)
  local cmd, rest = (msg or ""):match("^(%S*)%s*(.-)$")
  cmd = (cmd or ""):lower()
  if cmd == "bars" then
    outOfCombat(applyGuideLayout, "Bar layout")
  elseif cmd == "heal" then
    switchMode("heal")
  elseif cmd == "quest" or cmd == "bear" then
    switchMode("quest")
  elseif cmd == "healset" then
    saveGearSet("heal")
  elseif cmd == "questset" or cmd == "bearset" then
    saveGearSet("quest")
  elseif cmd == "save" and rest ~= "" then
    DruidKitDB.layouts[rest] = captureBars()
    say("saved layout '" .. rest .. "'.")
  elseif cmd == "load" and rest ~= "" then
    local l = DruidKitDB.layouts[rest]
    if not l then say("no layout called '" .. rest .. "'. Type /dk list."); return end
    outOfCombat(function() say(("loaded '%s' (%d buttons)."):format(rest, restoreBars(l))); askReload() end, "Loading '" .. rest .. "'")
  elseif cmd == "list" then
    local names = {}
    for k in pairs(DruidKitDB.layouts) do table.insert(names, k) end
    say(#names > 0 and ("saved layouts: " .. table.concat(names, ", ")) or "no saved layouts yet.")
  elseif cmd == "herbs" then
    herbsOn()
  elseif cmd == "keys" then
    DruidKit_SetDefaultKeys()
  elseif not (DruidKit_HelperCommand and DruidKit_HelperCommand(cmd, rest)) then
    say("/dk bars \194\183 heal \194\183 quest \194\183 healset \194\183 questset \194\183 save NAME \194\183 load NAME \194\183 list \194\183 herbs \194\183 bags \194\183 Full list: Help tab (Alt+6)")
    say("/dk catchup [level] \194\183 tracker/hud/rest/trainers on or off \194\183 unlock \194\183 lock")
  end
end

-- ---------------------------------------------------------------------------
-- In-game guide: a tabbed, Druid-styled window. Content comes from DruidKit_Guide.lua,
-- which Claude rewrites on request; /reload picks up the new version.
-- ---------------------------------------------------------------------------
local DRUID = "|cffff7c0a"      -- Druid class colour
local LEAF  = "|cff7fd35b"      -- nature green
local GREY  = "|cff9d9d9d"
local guideFrame

local function icon(path, size)
  if not path or path == "" then return "" end
  if not path:find("\\") then path = "Interface\\Icons\\" .. path end
  return ("|T%s:%d:%d:0:0|t "):format(path, size or 16, size or 16)
end

local function guideTabs()
  local g = DruidKitGuide
  if not g then return { { name = "Guide", lines = { "No guide yet. Ask Claude to update it, then /reload." } } } end
  if g.tabs then return g.tabs end
  return { { name = "Guide", sections = g.sections } }   -- older single-page format
end

-- One chunk of text per section. A single huge FontString (the Now tab is ~9,000 characters)
-- flickers and drops lines while you move, so each section gets its own.
local function tabChunks(tab)
  if tab.lines then return { table.concat(tab.lines, "\n") } end
  local chunks = {}
  for _, s in ipairs(tab.sections or {}) do
    local out = { icon(s.icon, 18) .. DRUID .. s.title .. "|r" }
    for _, line in ipairs(s.lines or {}) do
      local l = line:gsub("^%- ", LEAF .. "\226\128\162|r ")
      table.insert(out, "   " .. l)
    end
    table.insert(chunks, table.concat(out, "\n"))
  end
  return chunks
end

local function layoutParts(f)
  local w = (f.content:GetWidth() or 430) - 4
  local total = 0
  for i, fs in ipairs(f.parts) do
    if fs:IsShown() then
      fs:SetWidth(w)
      total = total + fs:GetStringHeight() + 14
    end
  end
  f.content:SetHeight(total + 24)
end

local function newFrame(kind, name, parent, template)
  local ok, f = pcall(CreateFrame, kind, name, parent, template)
  if ok and f then return f end
  return CreateFrame(kind, name, parent, "BasicFrameTemplateWithInset")
end

local function styleTab(b, selected)
  if selected then
    b.bg:SetColorTexture(0.10, 0.26, 0.10, 0.95)
    b.line:Show()
    b.label:SetFontObject("GameFontHighlightSmall")
  else
    b.bg:SetColorTexture(0, 0, 0, 0.45)
    b.line:Hide()
    b.label:SetFontObject("GameFontNormalSmall")
  end
end

-- Jump bar: one button per section of the open tab, so you never have to scroll to find a loop.
local function shortLabel(sec)
  if sec.short and sec.short ~= "" then return sec.short end
  local t = (sec.title or ""):gsub("|c%x%x%x%x%x%x%x%x", ""):gsub("|r", "")
  local loop = t:match("^Loop (%d+)")
  if loop then return "Loop " .. loop end
  return (t:match("^([^:%(,]+)") or t):sub(1, 10)
end
local function jumpTo(f, i)
  local y = 0
  for j = 1, i - 1 do
    local fs = f.parts[j]
    if fs and fs:IsShown() then y = y + fs:GetStringHeight() + 14 end
  end
  local max = f.scroll:GetVerticalScrollRange() or 0
  f.scroll:SetVerticalScroll(math.min(y, max))
end
local function layoutJump(f, tab)
  f.jumpButtons = f.jumpButtons or {}
  local secs = (tab and tab.sections) or {}
  local n = #secs
  local gap = 3
  local w = n > 0 and (((f.jumpBar:GetWidth() or 440) - gap * (n - 1)) / n) or 0
  for i = 1, math.max(n, #f.jumpButtons) do
    local b = f.jumpButtons[i]
    if i <= n then
      if not b then
        b = CreateFrame("Button", nil, f.jumpBar)
        b.bg = b:CreateTexture(nil, "BACKGROUND"); b.bg:SetAllPoints(); b.bg:SetColorTexture(0.10, 0.26, 0.10, 0.55)
        b.hl = b:CreateTexture(nil, "HIGHLIGHT"); b.hl:SetAllPoints(); b.hl:SetColorTexture(0.5, 0.83, 0.36, 0.25)
        b.label = b:CreateFontString(nil, "OVERLAY", "GameFontHighlightSmall")
        b.label:SetPoint("LEFT", 1, 0); b.label:SetPoint("RIGHT", -1, 0); b.label:SetWordWrap(false)
        f.jumpButtons[i] = b
      end
      b:ClearAllPoints()
      b:SetPoint("TOPLEFT", f.jumpBar, "TOPLEFT", (i - 1) * (w + gap), 0)
      b:SetSize(w, 22)
      b.label:SetText(shortLabel(secs[i]))
      local idx = i
      b:SetScript("OnClick", function() jumpTo(f, idx) end)
      b:SetScript("OnEnter", function(s)
        GameTooltip:SetOwner(s, "ANCHOR_BOTTOM"); GameTooltip:SetText(secs[idx].title or "", 1, 0.49, 0.04, 1, true); GameTooltip:Show()
      end)
      b:SetScript("OnLeave", function() GameTooltip:Hide() end)
      b:Show()
    elseif b then
      b:Hide()
    end
  end
end

local function selectTab(f, index)
  local tabs = guideTabs()
  index = math.max(1, math.min(index, #tabs))
  f.selected = index
  DruidKitDB.guideTab = index
  local chunks = tabChunks(tabs[index])
  for i, chunk in ipairs(chunks) do
    local fs = f.parts[i]
    if not fs then
      fs = f.content:CreateFontString(nil, "OVERLAY", "GameFontHighlight")
      fs:SetJustifyH("LEFT"); fs:SetJustifyV("TOP"); fs:SetSpacing(3)
      fs:SetPoint("TOPLEFT", f.parts[i - 1], "BOTTOMLEFT", 0, -14)
      f.parts[i] = fs
    end
    fs:SetText(chunk); fs:Show()
  end
  for i = #chunks + 1, #f.parts do f.parts[i]:SetText(""); f.parts[i]:Hide() end
  -- "Go" button on sections that have a place: sets the navigation arrow.
  f.goButtons = f.goButtons or {}
  local secs = tabs[index].sections or {}
  for i = 1, math.max(#chunks, #f.goButtons) do
    local go = secs[i] and secs[i].go
    local b = f.goButtons[i]
    if go and DruidKit_GoTo then
      if not b then
        b = CreateFrame("Button", nil, f.content, "UIPanelButtonTemplate")
        b:SetSize(44, 20); b:SetText("Go")
        f.goButtons[i] = b
      end
      b:ClearAllPoints(); b:SetPoint("TOPRIGHT", f.parts[i], "TOPRIGHT", 0, 2)
      b:SetScript("OnClick", function() DruidKit_GoTo(go.zone, go.x, go.y, go.label ~= "" and go.label or nil) end)
      b:SetScript("OnEnter", function(s)
        GameTooltip:SetOwner(s, "ANCHOR_LEFT"); GameTooltip:SetText(("Show the way: %s %.1f, %.1f"):format(go.zone, go.x, go.y), 1, 1, 1, 1, true); GameTooltip:Show()
      end)
      b:SetScript("OnLeave", function() GameTooltip:Hide() end)
      b:Show()
    elseif b then
      b:Hide()
    end
  end
  layoutParts(f)
  f.scroll:SetVerticalScroll(0)
  if f.jumpBar then pcall(layoutJump, f, tabs[index]) end
  for i, b in ipairs(f.tabButtons or {}) do styleTab(b, i == index) end
end

-- Even-width tab bar across the top of the window, so tabs never overlap whatever the size.
local function layoutTabs(f)
  local n = #(f.tabButtons or {})
  if n == 0 then return end
  local gap = 3
  local w = ((f.tabBar:GetWidth() or 480) - gap * (n - 1)) / n
  for i, b in ipairs(f.tabButtons) do
    b:ClearAllPoints()
    b:SetPoint("TOPLEFT", f.tabBar, "TOPLEFT", (i - 1) * (w + gap), 0)
    b:SetSize(w, 24)
  end
end

local function buildTabs(f)
  for _, b in ipairs(f.tabButtons or {}) do b:Hide() end
  f.tabButtons = {}
  local tabs = guideTabs()
  for i, t in ipairs(tabs) do
    local b = CreateFrame("Button", nil, f.tabBar)
    b.bg = b:CreateTexture(nil, "BACKGROUND"); b.bg:SetAllPoints()
    b.edge = b:CreateTexture(nil, "BORDER")
    b.edge:SetPoint("TOPLEFT", -1, 1); b.edge:SetPoint("BOTTOMRIGHT", 1, -1)
    b.edge:SetColorTexture(1, 0.49, 0.04, 0.25)
    b.bg:SetDrawLayer("BACKGROUND", 1); b.edge:SetDrawLayer("BACKGROUND", 0)
    b.line = b:CreateTexture(nil, "ARTWORK")
    b.line:SetHeight(2); b.line:SetPoint("BOTTOMLEFT", 0, 0); b.line:SetPoint("BOTTOMRIGHT", 0, 0)
    b.line:SetColorTexture(1, 0.49, 0.04, 1)
    local hl = b:CreateTexture(nil, "HIGHLIGHT"); hl:SetAllPoints(); hl:SetColorTexture(0.5, 0.83, 0.36, 0.15)
    b.label = b:CreateFontString(nil, "OVERLAY", "GameFontNormalSmall")
    b.label:SetPoint("LEFT", 1, 0); b.label:SetPoint("RIGHT", -1, 0)
    b.label:SetText(t.name); b.label:SetWordWrap(false)
    b:SetScript("OnClick", function()
      selectTab(f, i)
      if PlaySound and SOUNDKIT then pcall(PlaySound, SOUNDKIT.IG_CHARACTER_INFO_TAB) end
    end)
    b:SetScript("OnEnter", function(s)
      GameTooltip:SetOwner(s, "ANCHOR_BOTTOM")
      GameTooltip:AddLine(t.name, 1, 0.82, 0)
      GameTooltip:AddLine("Alt+" .. i, 0.7, 0.7, 0.7)
      GameTooltip:Show()
    end)
    b:SetScript("OnLeave", function() GameTooltip:Hide() end)
    b:Show()
    f.tabButtons[i] = b
  end
  layoutTabs(f)
end

local function buildGuide()
  local f = newFrame("Frame", "DruidKitGuideFrame", UIParent, "PortraitFrameTemplate")
  local saved = DruidKitDB and DruidKitDB.guideFrame
  f:SetSize(saved and saved.w or 500, saved and saved.h or 560)
  if saved and saved.point then
    f:SetPoint(saved.point, UIParent, saved.relPoint or saved.point, saved.x or 0, saved.y or 0)
  else
    f:SetPoint("CENTER", UIParent, "CENTER", 260, 0)
  end
  f:SetMovable(true); f:EnableMouse(true); f:SetClampedToScreen(true)
  f:SetResizable(true)
  if f.SetResizeBounds then f:SetResizeBounds(380, 320, 900, 1000)
  elseif f.SetMinResize then f:SetMinResize(380, 320); f:SetMaxResize(900, 1000) end
  f:RegisterForDrag("LeftButton")

  local function remember()
    local point, _, relPoint, x, y = f:GetPoint(1)
    DruidKitDB.guideFrame = { point = point, relPoint = relPoint, x = x, y = y, w = f:GetWidth(), h = f:GetHeight() }
  end
  f:SetScript("OnDragStart", f.StartMoving)
  f:SetScript("OnDragStop", function() f:StopMovingOrSizing(); remember() end)

  -- Resize grip, bottom-right corner
  local grip = CreateFrame("Button", nil, f)
  grip:SetSize(16, 16)
  grip:SetPoint("BOTTOMRIGHT", f, "BOTTOMRIGHT", -4, 4)
  grip:SetFrameLevel(f:GetFrameLevel() + 10)
  grip:SetNormalTexture("Interface\\ChatFrame\\UI-ChatIM-SizeGrabber-Up")
  grip:SetHighlightTexture("Interface\\ChatFrame\\UI-ChatIM-SizeGrabber-Highlight")
  grip:SetPushedTexture("Interface\\ChatFrame\\UI-ChatIM-SizeGrabber-Down")
  grip:SetScript("OnMouseDown", function() f:StartSizing("BOTTOMRIGHT") end)
  grip:SetScript("OnMouseUp", function() f:StopMovingOrSizing(); remember() end)
  f:SetFrameStrata("DIALOG")
  table.insert(UISpecialFrames, "DruidKitGuideFrame")

  -- Druid portrait and title
  local portraitIcon = "Interface\\Icons\\Ability_Druid_Maul"
  if f.SetPortraitToAsset then pcall(f.SetPortraitToAsset, f, portraitIcon)
  elseif f.portrait and SetPortraitToTexture then pcall(SetPortraitToTexture, f.portrait, portraitIcon) end
  if f.SetTitle then pcall(f.SetTitle, f, (DruidKitGuide and DruidKitGuide.title) or "Druid Kit Guide")
  else
    local title = f:CreateFontString(nil, "OVERLAY", "GameFontHighlight")
    title:SetPoint("TOP", f, "TOP", 0, -6)
    title:SetText((DruidKitGuide and DruidKitGuide.title) or "Druid Kit Guide")
  end

  -- Inset panel with a faint Restoration-tree backdrop and a deep green tint
  -- Tab bar under the title
  f.tabBar = CreateFrame("Frame", nil, f)
  f.tabBar:SetPoint("TOPLEFT", f, "TOPLEFT", 12, -60)
  f.tabBar:SetPoint("TOPRIGHT", f, "TOPRIGHT", -10, -60)
  f.tabBar:SetHeight(24)
  f.tabBar:SetScript("OnSizeChanged", function() layoutTabs(f) end)

  local inset = CreateFrame("Frame", nil, f, "InsetFrameTemplate")
  inset:SetPoint("TOPLEFT", f, "TOPLEFT", 10, -90)
  inset:SetPoint("BOTTOMRIGHT", f, "BOTTOMRIGHT", -8, 30)
  local bg = inset:CreateTexture(nil, "BACKGROUND", nil, 1)
  bg:SetPoint("TOPLEFT", 3, -3); bg:SetPoint("BOTTOMRIGHT", -3, 3)
  if bg:SetTexture("Interface\\TalentFrame\\DruidRestoration-TopLeft") == false then bg:Hide() end
  bg:SetAlpha(0.35)
  local tint = inset:CreateTexture(nil, "BACKGROUND", nil, 2)
  tint:SetAllPoints(bg)
  tint:SetColorTexture(0.03, 0.10, 0.04, 0.55)

  -- Subtitle: last updated
  local sub = f:CreateFontString(nil, "OVERLAY", "GameFontNormalSmall")
  sub:SetPoint("TOPLEFT", f, "TOPLEFT", 64, -38)
  f.sub = sub

  -- Footer hint
  local hint = f:CreateFontString(nil, "OVERLAY", "GameFontDisableSmall")
  hint:SetPoint("BOTTOMRIGHT", f, "BOTTOMRIGHT", -24, 10)
  hint:SetText("Alt+1-8 tabs  \194\183  Shift+J to close  \194\183  ask Claude to \"update\", then /reload")

  local jumpBar = CreateFrame("Frame", nil, inset)
  jumpBar:SetPoint("TOPLEFT", inset, "TOPLEFT", 8, -6)
  jumpBar:SetPoint("TOPRIGHT", inset, "TOPRIGHT", -8, -6)
  jumpBar:SetHeight(22)
  jumpBar:SetScript("OnSizeChanged", function() if f.selected then pcall(layoutJump, f, guideTabs()[f.selected]) end end)
  f.jumpBar = jumpBar
  local scroll = CreateFrame("ScrollFrame", nil, inset, "UIPanelScrollFrameTemplate")
  scroll:SetPoint("TOPLEFT", inset, "TOPLEFT", 10, -34)
  scroll:SetPoint("BOTTOMRIGHT", inset, "BOTTOMRIGHT", -28, 8)
  local content = CreateFrame("Frame", nil, scroll)
  content:SetSize(430, 10)
  scroll:SetScrollChild(content)
  local text = content:CreateFontString(nil, "OVERLAY", "GameFontHighlight")
  text:SetPoint("TOPLEFT", 2, -2)
  text:SetWidth(426)
  scroll:SetScript("OnSizeChanged", function(_, w)
    if not w or w <= 0 then return end
    content:SetWidth(w)
    if f.parts then layoutParts(f) end
  end)
  text:SetJustifyH("LEFT"); text:SetJustifyV("TOP")
  text:SetSpacing(3)
  f.scroll, f.content, f.text = scroll, content, text
  f.parts = { text }

  f:Hide()
  return f
end

local function showGuide()
  guideFrame = guideFrame or buildGuide()
  if guideFrame:IsShown() then guideFrame:Hide(); return end
  buildTabs(guideFrame)
  guideFrame.sub:SetText(GREY .. "Updated " .. ((DruidKitGuide and DruidKitGuide.updated) or "?") .. "|r")
  selectTab(guideFrame, (DruidKitDB and DruidKitDB.guideTab) or 1)
  guideFrame:Show()
  if PlaySound and SOUNDKIT then pcall(PlaySound, SOUNDKIT.IG_SPELLBOOK_OPEN) end
end

local function openGuideTab(index)
  guideFrame = guideFrame or buildGuide()
  if guideFrame:IsShown() and guideFrame.selected == index then guideFrame:Hide(); return end
  buildTabs(guideFrame)
  guideFrame.sub:SetText(GREY .. "Updated " .. ((DruidKitGuide and DruidKitGuide.updated) or "?") .. "|r")
  selectTab(guideFrame, index)
  guideFrame:Show()
end

SLASH_DRUIDKITGUIDE1 = "/guide"
SlashCmdList["DRUIDKITGUIDE"] = function(msg)
  local n = tonumber(msg or "")
  if n then openGuideTab(n) else showGuide() end
end

-- ---------------------------------------------------------------------------
-- Keybinding (Options > Keybindings > AddOns > Druid Kit) and an Options > AddOns page
-- ---------------------------------------------------------------------------
BINDING_HEADER_DRUIDKIT = "Druid Kit"
BINDING_NAME_DRUIDKIT_TOGGLEGUIDE = "Open / close guide"
BINDING_NAME_DRUIDKIT_BAGS = "Open / close Bag check"
function DruidKit_ToggleGuide() showGuide() end
local TAB_NAMES = { "Now", "Quests", "Combat", "World", "Crafting", "Help", "Talents", "Dungeons" }
for i, n in ipairs(TAB_NAMES) do
  _G["BINDING_NAME_DRUIDKIT_TAB" .. i] = "Guide: " .. n .. " tab"
end
function DruidKit_OpenTab(i) openGuideTab(i) end

local DEFAULT_GUIDE_KEY = "SHIFT-J"
local function setDefaultTabKeys()
  if InCombatLockdown() then return end
  DruidKitDB.tabKeyDone = DruidKitDB.tabKeyDone or {}
  if DruidKitDB.tabKeysSet then for i = 1, 5 do DruidKitDB.tabKeyDone[i] = true end end
  local set = 0
  for i = 1, #TAB_NAMES do
    if not DruidKitDB.tabKeyDone[i] then
      DruidKitDB.tabKeyDone[i] = true
      local key = "ALT-" .. i
      local current = GetBindingAction and GetBindingAction(key)
      if not (GetBindingKey and GetBindingKey("DRUIDKIT_TAB" .. i)) and (current == nil or current == "") then
        safe(SetBinding, key, "DRUIDKIT_TAB" .. i); set = set + 1
      end
    end
  end
  if set > 0 then
    safe(SaveBindings, GetCurrentBindingSet and GetCurrentBindingSet() or 1)
    say(("Alt+1-%d open the guide tabs: %s."):format(#TAB_NAMES, table.concat(TAB_NAMES, ", ")))
  end
end

local function setDefaultGoKey()
  if DruidKitDB.goKeySet or InCombatLockdown() then return end
  DruidKitDB.goKeySet = true
  if GetBindingKey and GetBindingKey("DRUIDKIT_GOTO") then return end
  local current = GetBindingAction and GetBindingAction("ALT-G")
  if current == nil or current == "" then
    safe(SetBinding, "ALT-G", "DRUIDKIT_GOTO")
    safe(SaveBindings, GetCurrentBindingSet and GetCurrentBindingSet() or 1)
    say("Alt+G opens Go to: trainers, bank, auction house and more.")
  else
    say("Alt+G is taken. Set a key for Go to in Options > Keybindings > AddOns > Druid Kit, or type /dk go.")
  end
end

local function setDefaultBagsKey()
  if DruidKitDB.bagsKeySet or InCombatLockdown() then return end
  DruidKitDB.bagsKeySet = true
  if GetBindingKey and GetBindingKey("DRUIDKIT_BAGS") then return end
  local current = GetBindingAction and GetBindingAction("ALT-B")
  if current == nil or current == "" then
    safe(SetBinding, "ALT-B", "DRUIDKIT_BAGS")
    safe(SaveBindings, GetCurrentBindingSet and GetCurrentBindingSet() or 1)
    say("Alt+B opens and closes the Bag check.")
  else
    say("Alt+B is taken. Set a key for Bag check in Options > Keybindings > AddOns > Druid Kit.")
  end
end

-- Autorun on Option+W (ALT-W), or Ctrl+W if that's taken. The ` key stays as a spare.
local function setAutorunAltW()
  if DruidKitDB.autorunAltW or InCombatLockdown() then return end
  DruidKitDB.autorunAltW = true
  for _, key in ipairs({ "ALT-W", "CTRL-W" }) do
    local current = GetBindingAction and GetBindingAction(key)
    if current == "TOGGLEAUTORUN" then say(key == "ALT-W" and "Option+W already toggles autorun." or "Ctrl+W already toggles autorun.") return end
    if current == nil or current == "" then
      safe(SetBinding, key, "TOGGLEAUTORUN")
      safe(SaveBindings, GetCurrentBindingSet and GetCurrentBindingSet() or 1)
      say(key == "ALT-W" and "Option+W now toggles autorun." or "Option+W was taken, so Ctrl+W now toggles autorun.")
      return
    end
  end
  say("Option+W and Ctrl+W are both taken. Set autorun in Options > Keybindings > Movement > Toggle Autorun.")
end

local function setDefaultAutorunKey()
  pcall(setAutorunAltW)
  if DruidKitDB.autorunKeySet or InCombatLockdown() then return end
  DruidKitDB.autorunKeySet = true
  local current = GetBindingAction and GetBindingAction("`")
  if current == "TOGGLEAUTORUN" then return end
  if current == nil or current == "" then
    safe(SetBinding, "`", "TOGGLEAUTORUN")
    safe(SaveBindings, GetCurrentBindingSet and GetCurrentBindingSet() or 1)
    say("the ` key (under Esc) now toggles autorun.")
  else
    say("the ` key is taken, so autorun wasn't bound. Set it in Options > Keybindings > Movement > Toggle Autorun.")
  end
end

local function setDefaultModeKey()
  if DruidKitDB.modeKeySet or InCombatLockdown() then return end
  DruidKitDB.modeKeySet = true
  if GetBindingKey and GetBindingKey("DRUIDKIT_TOGGLEMODE") then return end
  local current = GetBindingAction and GetBindingAction("ALT-H")
  if current == nil or current == "" then
    safe(SetBinding, "ALT-H", "DRUIDKIT_TOGGLEMODE")
    safe(SaveBindings, GetCurrentBindingSet and GetCurrentBindingSet() or 1)
    say("Alt+H switches between healing and questing mode.")
  end
end

local function setDefaultGuideKey()
  if DruidKitDB.guideKeySet or InCombatLockdown() then return end
  DruidKitDB.guideKeySet = true
  if GetBindingKey and GetBindingKey("DRUIDKIT_TOGGLEGUIDE") then return end
  local current = GetBindingAction and GetBindingAction(DEFAULT_GUIDE_KEY)
  if current == nil or current == "" then
    safe(SetBinding, DEFAULT_GUIDE_KEY, "DRUIDKIT_TOGGLEGUIDE")
    safe(SaveBindings, GetCurrentBindingSet and GetCurrentBindingSet() or 1)
    say("Shift+J now opens your guide. Change it in Options > Keybindings > AddOns.")
  end
end

function DruidKit_SetDefaultKeys()
  if InCombatLockdown() then say("after combat, please."); return end
  pcall(setDefaultGuideKey); pcall(setDefaultTabKeys); pcall(setDefaultBagsKey); pcall(setDefaultGoKey); pcall(setDefaultAutorunKey); pcall(setDefaultModeKey)
  say("keys checked.")
  askReload()
end

local function buildOptionsPage()
  if not (Settings and Settings.RegisterCanvasLayoutCategory and Settings.RegisterAddOnCategory) then return end
  local panel = CreateFrame("Frame")
  panel.name = "Druid Kit"
  local t = panel:CreateFontString(nil, "ARTWORK", "GameFontNormalLarge")
  t:SetPoint("TOPLEFT", 16, -16)
  t:SetText("Druid Kit")
  local d = panel:CreateFontString(nil, "ARTWORK", "GameFontHighlight")
  d:SetPoint("TOPLEFT", t, "BOTTOMLEFT", 0, -8)
  d:SetWidth(560); d:SetJustifyH("LEFT")
  d:SetText("Guide: Shift+J or /guide; Alt+1-8 jump to a tab.   Bars: /dk bars (undo: /dk load backup).   Find Herbs: /dk herbs.\nPanels: /dk unlock to move, /dk lock.   Catch-up target: /dk catchup 22.   /dk hud, rest, tracker or trainers off to hide.\nChange the guide key in Options > Keybindings > AddOns > Druid Kit.")
  local b = CreateFrame("Button", nil, panel, "UIPanelButtonTemplate")
  b:SetSize(160, 26)
  b:SetPoint("TOPLEFT", d, "BOTTOMLEFT", 0, -12)
  b:SetText("Open guide")
  b:SetScript("OnClick", function()
    if SettingsPanel and SettingsPanel:IsShown() then HideUIPanel(SettingsPanel) end
    showGuide()
  end)
  local category = Settings.RegisterCanvasLayoutCategory(panel, "Druid Kit")
  Settings.RegisterAddOnCategory(category)
end

local setup = CreateFrame("Frame")
setup:RegisterEvent("PLAYER_ENTERING_WORLD")
setup:SetScript("OnEvent", function(self)
  self:UnregisterEvent("PLAYER_ENTERING_WORLD")
  DruidKitDB = DruidKitDB or {}
  pcall(buildOptionsPage)
  -- Key bindings are never changed at login (that taints the action bars). Just say if a default is missing.
  C_Timer.After(5, function()
    local missing = {}
    for i = 1, #TAB_NAMES do
      if not (GetBindingKey and GetBindingKey("DRUIDKIT_TAB" .. i)) and not (DruidKitDB.tabKeyDone and DruidKitDB.tabKeyDone[i]) then table.insert(missing, "Alt+" .. i) end
    end
    if #missing > 0 then say("new guide key " .. table.concat(missing, ", ") .. " not set yet: type /dk keys (then reload).") end
  end)
end)


-- ---------------------------------------------------------------------------
-- Auto attack watch: in Bear or Cat Form, in combat, next to your target and not swinging?
-- A big "AUTO ATTACK OFF: press R" appears (words, not colour). Addons can't start attacks
-- themselves, so you press R (or any bear/cat ability: they all start auto attack now).
-- ---------------------------------------------------------------------------
do
  local warn = CreateFrame("Frame", "DruidKitAttackWarn", UIParent)
  warn:SetSize(420, 40); warn:SetPoint("CENTER", 0, -120); warn:SetFrameStrata("HIGH")
  warn.text = warn:CreateFontString(nil, "OVERLAY")
  warn.text:SetFont("Fonts\\FRIZQT__.TTF", 24, "THICKOUTLINE"); warn.text:SetAllPoints()
  warn.text:SetText("AUTO ATTACK OFF: press R"); warn.text:SetTextColor(1, 1, 1)
  warn:Hide()
  local function bool(fn, ...)
    local ok, v = pcall(fn, ...)
    if ok and type(v) == "boolean" then return v end
    if ok and type(v) == "number" then return v == 1 end
  end
  local offFor, acc = 0, 0
  local f = CreateFrame("Frame")
  f:SetScript("OnUpdate", function(_, el)
    acc = acc + el
    if acc < 0.25 then return end
    local step = acc; acc = 0
    local show = false
    if DruidKitDB and DruidKitDB.attackWarn ~= false and UnitAffectingCombat and UnitAffectingCombat("player")
       and GetShapeshiftForm and (GetShapeshiftForm() or 0) > 0 and UnitExists("target") and not UnitIsDead("target")
       and UnitCanAttack("player", "target") then
      local swinging = IsCurrentSpell and bool(IsCurrentSpell, 6603)
      local close = CheckInteractDistance and bool(CheckInteractDistance, "target", 3)
      if swinging == false and close == true then show = true end
    end
    offFor = show and (offFor + step) or 0
    if offFor >= 1.5 then warn:Show() else warn:Hide() end
  end)
end
