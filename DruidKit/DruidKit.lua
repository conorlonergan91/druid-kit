-- Druid Kit
--   /dk bars          lay out action bars and keys to match the Combat Guide (known spells only)
--   /dk save NAME     save your current bars as a named layout
--   /dk load NAME     load a saved layout ("/dk load backup" goes back to before your first /dk bars)
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
-- Window places: every frame's default spot { point, relPoint on UIParent, x, y }, in one table. A dragged frame
-- keeps its own spot (DruidKitDB.pos); /dk resetpos clears them. Layout and reasons: FEATURES "Window positions".
-- ---------------------------------------------------------------------------
local POS = {
  -- travel: where the eye goes while moving
  arrow    = { "TOP", "TOP", 0, -215, frame = "DruidKitArrow" },
  steps    = { "BOTTOMRIGHT", "BOTTOMRIGHT", -10, 140, frame = "DruidKitSteps" },
  tracker  = { "TOPRIGHT", "TOPRIGHT", -220, -165, frame = "DruidKit_tracker" },
  herb     = { "TOPRIGHT", "TOPRIGHT", -220, -280, frame = "DruidKitHerbButton" },
  -- combat: near the middle, never on it
  party    = { "TOPLEFT", "TOPLEFT", 10, -140, frame = "DruidKitParty", secure = true },
  rolls    = { "TOP", "TOP", 0, -8, frame = "DruidKitRolls" },
  warn     = { "CENTER", "CENTER", 0, -238, frame = "DruidKitAttackWarn" },
  -- out of combat only
  rest     = { "CENTER", "CENTER", 0, -140, frame = "DruidKit_rest" },
  hud      = { "CENTER", "CENTER", 0, -190, frame = "DruidKit_hud" },
  questxp  = { "BOTTOM", "BOTTOM", 0, 60, frame = "DruidKitQuestXP" },   -- only when there is no XP bar to sit on
  -- reading windows: the left panel slot, where the game opens the quest log and spellbook
  guide    = { "TOPLEFT", "TOPLEFT", 20, -104, frame = "DruidKitGuideFrame" },
  lore     = { "TOPLEFT", "TOPLEFT", 20, -104, frame = "DruidKitLore" },
  dungeons = { "TOPLEFT", "TOPLEFT", 20, -104, frame = "DruidKitDungeonQuests" },
  share    = { "TOPLEFT", "TOPLEFT", 20, -104, frame = "DruidKitQuestShare" },
  ["goto"] = { "TOPLEFT", "TOPLEFT", 20, -104, frame = "DruidKitGoTo" },
  keys     = { "TOPLEFT", "TOPLEFT", 20, -104, frame = "DruidKitKeymap" },
  -- item lists: beside the bags (bottom right), which open with the vendor, the bank and loot
  bags     = { "RIGHT", "RIGHT", -240, 0, frame = "DruidKitBagCheck" },
  bank     = { "RIGHT", "RIGHT", -240, 0, frame = "DruidKitBankCheck" },
  loot     = { "RIGHT", "RIGHT", -240, 0, frame = "DruidKitLootHelp" },
}
local BYFRAME = {}
for name, p in pairs(POS) do BYFRAME[p.frame] = name end
-- Spots saved before DruidKitDB.pos: still read, cleared by a reset.
local OLDKEY = { steps = "stepsPos", arrow = "arrowPos", party = "partyPos3" }
local function oldSpot(db, name)
  if name == "guide" then
    local g = db.guideFrame
    return g and g.point and { g.point, g.relPoint or g.point, g.x or 0, g.y or 0 }
  end
  local p = OLDKEY[name] and db[OLDKEY[name]] or db.panels and db.panels[name]
  local at = name == "steps" and "TOPRIGHT" or "CENTER"   -- older steps/arrow saves kept only x, y
  if p and #p == 2 then return { at, at, p[1], p[2] } end
  return p
end
local function keyOf(f, name) return name or BYFRAME[f.GetName and f:GetName() or ""] end

DruidKitPos = { DEFAULT = POS }
function DruidKitPos.saved(name)
  local db = DruidKitDB
  if not db or not name then return nil end
  return db.pos and db.pos[name] or oldSpot(db, name)
end
-- name defaults to the frame's own (by its global name). Default offsets are screen units, whatever the frame's scale.
function DruidKitPos.place(f, name)
  name = keyOf(f, name)
  local s, d = DruidKitPos.saved(name), POS[name]
  if not (s or d) then return end
  f:ClearAllPoints()
  if s then f:SetPoint(s[1], UIParent, s[2], s[3], s[4]); return end
  local k = f.GetScale and f:GetScale() or 1
  f:SetPoint(d[1], UIParent, d[2], d[3] / k, d[4] / k)
end
function DruidKitPos.save(f, name)
  name = keyOf(f, name)
  local p, _, rp, x, y = f:GetPoint(1)
  if not (name and p and DruidKitDB) then return end
  DruidKitDB.pos = DruidKitDB.pos or {}
  DruidKitDB.pos[name] = { p, rp or p, x or 0, y or 0 }
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
  { slot = 9,   spell = "Omen of Clarity" },     -- self buff (level 20): refresh now and then
  { slot = 11,  spell = "Starfire" },            -- level 20, key -
  { slot = 12,  spell = "Rebirth" },             -- level 20, key =
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
  { slot = 62,  spell = "Cure Poison" },         -- bottom-left, no key: click it
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
    if kind then
      layout[slot] = { kind = kind, id = id, name = kind == "macro" and GetMacroInfo and safe(GetMacroInfo, id) or nil }
    end
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
        local idx = a.id
        if a.name then idx = GetMacroIndexByName and safe(GetMacroIndexByName, a.name) or 0 end
        if idx and idx ~= 0 then safe(PickupMacro, idx); ok = GetCursorInfo() ~= nil end
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
local pending = {}
local function defer(fn, key)
  key = key or fn
  for _, p in ipairs(pending) do if p.key == key then return false end end
  table.insert(pending, { key = key, fn = fn })
  return true
end
local function runPending()
  local list = pending
  pending = {}
  for _, p in ipairs(list) do
    local ok, err = pcall(p.fn)
    if not ok and geterrorhandler then geterrorhandler()(err) end
  end
end
local function outOfCombat(fn, label)
  if InCombatLockdown() then
    if defer(fn, label) then say(label .. " will run when combat ends.") end
  else
    fn()
  end
end

-- /dk resetpos [name]: forget saved spots and put frames back now. Frames holding secure buttons move after combat.
-- Only movable frames ever leave their default, so only they are moved.
function DruidKitPos.reset(only)
  if only and not POS[only] then
    local names = {}
    for n in pairs(POS) do names[#names + 1] = n end
    table.sort(names)
    say(("no window called '%s'. Names: %s."):format(only, table.concat(names, ", ")))
    return
  end
  local db = DruidKitDB or {}
  local done, later = {}, {}
  for name, d in pairs(POS) do
    if not only or only == name then
      if db.pos then db.pos[name] = nil end
      if OLDKEY[name] then db[OLDKEY[name]] = nil end
      if db.panels then db.panels[name] = nil end
      if name == "guide" and db.guideFrame then db.guideFrame.point = nil end
      local f = _G[d.frame]
      local function put() DruidKitPos.place(f, name); if f.onPlaced then pcall(f.onPlaced) end end
      if f and f.IsMovable and f:IsMovable() and d.secure and InCombatLockdown() then
        defer(put, "pos:" .. name); later[#later + 1] = name
      else
        if f and f.IsMovable and f:IsMovable() then put() end
        done[#done + 1] = name
      end
    end
  end
  table.sort(done); table.sort(later)
  if #done > 0 then say("back to the default place: " .. table.concat(done, ", ") .. ".") end
  if #later > 0 then say("after combat: " .. table.concat(later, ", ") .. " (secure buttons can't move in combat).") end
end

-- Key bindings the layout takes, with what they were before, so /dk load backup can put them back.
local function captureKeys(keys)
  local old = {}
  for _, k in ipairs(keys) do old[k] = (GetBindingAction and safe(GetBindingAction, k)) or "" end
  return old
end
local function restoreKeys(old)
  if not old then return end
  for k, a in pairs(old) do
    if a == "" then safe(SetBinding, k) else safe(SetBinding, k, a) end
  end
  safe(SaveBindings, GetCurrentBindingSet and GetCurrentBindingSet() or 1)
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
  local firstBackup = not DruidKitDB.layouts.backup
  if firstBackup then DruidKitDB.layouts.backup = captureBars() end
  local backup = DruidKitDB.layouts.backup
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
  local keys = {}
  for _, b in ipairs(BINDINGS) do table.insert(keys, b.key) end
  local catKey = not DruidKitDB.catKeySet and SetBindingSpell and isKnown("Cat Form")
  if catKey then table.insert(keys, "G") end
  backup.keys = backup.keys or {}
  for k, a in pairs(captureKeys(keys)) do
    if backup.keys[k] == nil then backup.keys[k] = a end
  end
  for _, b in ipairs(BINDINGS) do safe(SetBinding, b.key, b.action) end
  if catKey and safe(SetBindingSpell, "G", "Cat Form") ~= false then DruidKitDB.catKeySet, DruidKitDB.catKeyBy = "G", "bars" end
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
  say(firstBackup and "Your old bars and keys are saved: type /dk load backup to undo."
    or "Your bars and keys from before your first /dk bars are still saved: /dk load backup goes back to them.")
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

-- /dk newspells: put every spell you know onto its empty layout key (out of combat, caster form). Fixes bars when
-- the layout gained spells you had already learned (level 20: Starfire, Rebirth, Omen of Clarity).
local fillEmptySlots

local function addNewSpells()
  if InCombatLockdown() then defer(addNewSpells); return end
  if GetShapeshiftForm and GetShapeshiftForm() ~= 0 then return end  -- spell lists change in forms; only check in caster form
  local now = knownLayoutSpells()
  local before = DruidKitDB.knownSpells
  DruidKitDB.knownSpells = now
  if not before then return end              -- first run: just remember what you know
  local added = {}
  for _, e in ipairs(currentLayout()) do
    if e.spell and now[e.spell] and not before[e.spell] then
      if #added == 0 then DruidKitDB.layouts = DruidKitDB.layouts or {}; DruidKitDB.layouts.autosave = captureBars() end
      if pickupEntry(e) then place(e.slot); table.insert(added, e.spell .. " (" .. slotKey(e.slot) .. ")") else ClearCursor() end
    end
  end
  if #added > 0 then
    say("new skill on your bars: " .. table.concat(added, ", ") .. ". /dk load autosave to undo.")
    askReload()
  end
end

fillEmptySlots = function()
  if GetShapeshiftForm and GetShapeshiftForm() ~= 0 then return nil end
  local list = {}
  for _, e in ipairs(currentLayout()) do
    if e.spell and not hasAction(e.slot) and isKnown(e.spell) then
      if pickupEntry(e) then place(e.slot); table.insert(list, e.spell .. " (" .. slotKey(e.slot) .. ")") else ClearCursor() end
    end
  end
  DruidKitDB.knownSpells = knownLayoutSpells()
  return list
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
      if pickupEntry(e) then place(e.slot); n = n + 1 else ClearCursor() end
    end
  end
  return n
end

-- explicit: asked by /dk heal or /dk quest, so the current mode re-wears its set; Alt+H back to it changes nothing.
local queuedMode, queuedExplicit
local function switchMode(mode, explicit)
  if InCombatLockdown() then
    queuedMode, queuedExplicit = mode, explicit
    defer(function()
      local m, ex = queuedMode, queuedExplicit; queuedMode, queuedExplicit = nil, nil
      if m and (ex or m ~= (DruidKitDB.barMode or "quest")) then switchMode(m, ex) end
    end, "mode")
    local name = mode == "heal" and "Healing" or "Questing"
    if mode ~= (DruidKitDB.barMode or "quest") then say(name .. " mode after combat.")
    elseif explicit then say("stays in " .. name:lower() .. " mode: gear re-worn after combat.")
    else say("stays in " .. name:lower() .. " mode.") end
    return
  end
  queuedMode, queuedExplicit = nil, nil
  DruidKitDB.layouts = DruidKitDB.layouts or {}
  local cur = DruidKitDB.barMode or "quest"
  local switched = cur ~= mode
  if switched then
    DruidKitDB.layouts["mode_" .. cur] = captureBars()
    DruidKitDB.barMode = mode
    local snap = DruidKitDB.layouts["mode_" .. mode]
    if snap then
      restoreBars(snap)
      fillLearned(layoutFor(mode))
    else
      applyGuideLayout()
    end
  end
  DruidKitDB.knownSpells = knownLayoutSpells()
  local missing, noSet = wearGearSet(mode)
  local label = mode == "heal" and "Healing mode" or "Questing mode"
  local gear = noSet and ("no " .. (mode == "heal" and "healing" or "questing") .. " set saved yet (/dk " .. mode .. "set)")
    or (missing > 0 and (missing .. " set piece(s) not in your bags: check the bank")
      or (switched and "gear swapped" or "gear re-worn"))
  say(label .. (switched and ": bars switched, " or ": ") .. gear .. ".")
  if switched then askReload() end
  if DruidKitBagsAPI and DruidKitBagsAPI.refresh then pcall(DruidKitBagsAPI.refresh) end
end

function DruidKit_ToggleMode()
  switchMode(((queuedMode or DruidKitDB.barMode) == "heal") and "quest" or "heal")
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
DruidKitPos.place(herbButton, "herb")
herbButton:SetText("Click to turn on Find Herbs")
herbButton:SetAttribute("type", "spell")
herbButton:SetAttribute("spell", "Find Herbs")
herbButton:RegisterForClicks("AnyUp", "AnyDown")
herbButton:Hide()
herbButton:HookScript("OnClick", function(self)
  C_Timer.After(0.5, function() if not InCombatLockdown() then self:Hide() end end)
end)

local function hideHerbButton()
  if InCombatLockdown() then defer(hideHerbButton) else herbButton:Hide() end
end

local function herbsOn()
  if not isKnown("Find Herbs") then return end
  local idx, active = findHerbsTrackingIndex()
  if active then hideHerbButton(); return end
  if idx and C_Minimap.SetTracking then safe(C_Minimap.SetTracking, idx, true) end
  C_Timer.After(1, function()
    local _, nowActive = findHerbsTrackingIndex()
    if nowActive then
      hideHerbButton()
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
    runPending()
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
  elseif cmd == "keymap" then
    if DruidKit_ShowKeymap then DruidKit_ShowKeymap() end
  elseif cmd == "newspells" then
    outOfCombat(function()
      local list = fillEmptySlots()
      if not list then say("change to caster form first, then /dk newspells again.")
      elseif #list == 0 then say("every spell you know already has its key.")
      else say("on your bars now: " .. table.concat(list, ", ") .. "."); askReload() end
    end, "Placing new spells")
  elseif cmd == "heal" then
    switchMode("heal", true)
  elseif cmd == "quest" or cmd == "bear" then
    switchMode("quest", true)
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
    outOfCombat(function()
      say(("loaded '%s' (%d buttons)."):format(rest, restoreBars(l)))
      restoreKeys(l.keys)
      if DruidKitDB.catKeyBy == "bars" and l.keys and l.keys[DruidKitDB.catKeySet] then
        DruidKitDB.catKeySet, DruidKitDB.catKeyBy = nil, nil
      end
      askReload()
    end, "Loading '" .. rest .. "'")
  elseif cmd == "list" then
    local names = {}
    for k in pairs(DruidKitDB.layouts) do table.insert(names, k) end
    say(#names > 0 and ("saved layouts: " .. table.concat(names, ", ")) or "no saved layouts yet.")
  elseif cmd == "herbs" then
    herbsOn()
  elseif cmd == "catkey" or cmd == "runkey" then
    local key, force = (rest or ""):match("^(%S*)%s*(%S*)")
    if key:lower() == "force" then key, force = "", "force" end
    key = key:gsub("^[Cc][Mm][Dd]%+", "META-")
    ;(cmd == "catkey" and DruidKit_SetCatKey or DruidKit_SetRunKey)(key, force == "force")
  elseif cmd == "keys" then
    DruidKit_SetDefaultKeys()
  elseif cmd == "resetpos" then
    DruidKitPos.reset(rest ~= "" and rest:lower() or nil)
  elseif (cmd == "steps" or cmd == "auto" or cmd == "arrow") and DruidKit_StepsCommand then
    DruidKit_StepsCommand(cmd == "steps" and rest or cmd)
  elseif not (DruidKit_HelperCommand and DruidKit_HelperCommand(cmd, rest)) then
    say("/dk bars \194\183 heal \194\183 quest \194\183 healset \194\183 questset \194\183 save NAME \194\183 load NAME \194\183 list \194\183 herbs \194\183 bags \194\183 Full list: Help tab (Alt+6)")
    say("/dk steps (show or hide steps + arrow, Alt+N) \194\183 steps reset \194\183 steps unskip \194\183 steps log \194\183 auto (quest auto accept/hand-in) \194\183 arrow")
    say("/dk catchup [level] \194\183 tracker/hud/rest/trainers on or off \194\183 unlock \194\183 lock \194\183 resetpos [name]")
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

local function newFrame(...)
  return (DruidKitStyle and DruidKitStyle.newFrame or CreateFrame)(...)
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

local function tabButton(f, i)
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
  b.label:SetWordWrap(false)
  b:SetScript("OnClick", function()
    selectTab(f, i)
    if PlaySound and SOUNDKIT then pcall(PlaySound, SOUNDKIT.IG_CHARACTER_INFO_TAB) end
  end)
  b:SetScript("OnEnter", function(s)
    GameTooltip:SetOwner(s, "ANCHOR_BOTTOM")
    GameTooltip:AddLine(s.tabName or "", 1, 0.82, 0)
    GameTooltip:AddLine("Alt+" .. i, 0.7, 0.7, 0.7)
    GameTooltip:Show()
  end)
  b:SetScript("OnLeave", function() GameTooltip:Hide() end)
  return b
end

local function buildTabs(f)
  f.tabPool = f.tabPool or {}
  f.tabButtons = {}
  local tabs = guideTabs()
  for i, t in ipairs(tabs) do
    local b = f.tabPool[i] or tabButton(f, i)
    f.tabPool[i] = b
    b.tabName = t.name
    b.label:SetText(t.name)
    b:Show()
    f.tabButtons[i] = b
  end
  for i = #tabs + 1, #f.tabPool do f.tabPool[i]:Hide() end
  layoutTabs(f)
end

local function buildGuide()
  local f = newFrame("Frame", "DruidKitGuideFrame", UIParent, "PortraitFrameTemplate")
  local saved = DruidKitDB and DruidKitDB.guideFrame
  f:SetSize(saved and saved.w or 500, saved and saved.h or 560)
  DruidKitPos.place(f, "guide")
  f:SetMovable(true); f:EnableMouse(true); f:SetClampedToScreen(true)
  f:SetResizable(true)
  if f.SetResizeBounds then f:SetResizeBounds(380, 320, 900, 1000)
  elseif f.SetMinResize then f:SetMinResize(380, 320); f:SetMaxResize(900, 1000) end
  f:RegisterForDrag("LeftButton")

  local function remember()
    DruidKitPos.save(f, "guide")
    DruidKitDB.guideFrame = { w = f:GetWidth(), h = f:GetHeight() }
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

local function setDefaultStepsKey()
  if DruidKitDB.stepsKeySet or InCombatLockdown() then return end
  DruidKitDB.stepsKeySet = true
  if GetBindingKey and GetBindingKey("DRUIDKIT_STEPS") then return end
  local current = GetBindingAction and GetBindingAction("ALT-N")
  if current == nil or current == "" then
    safe(SetBinding, "ALT-N", "DRUIDKIT_STEPS")
    safe(SaveBindings, GetCurrentBindingSet and GetCurrentBindingSet() or 1)
    say("Alt+N shows or hides the route steps and arrow.")
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

-- One key for one action, on request only, out of combat. Never takes a key in use unless forced.
-- Mac: Cmd is "META-" in a binding. If the client refuses it, SetBinding returns false and we say so.
local function keyName(k) return (k:gsub("META%-", "Cmd+"):gsub("CTRL%-", "Ctrl+"):gsub("ALT%-", "Option+"):gsub("SHIFT%-", "Shift+")) end
local function bindOne(key, action, label, force, spell)
  if InCombatLockdown() then say("after combat, please."); return false end
  local current = GetBindingAction and GetBindingAction(key)
  if current == action then say(keyName(key) .. " already " .. label .. "."); return true end
  if current and current ~= "" and not force then
    say(("%s is used for %s, so I didn't change it."):format(keyName(key), current)); return false
  end
  local ok
  if spell and SetBindingSpell then ok = safe(SetBindingSpell, key, spell) else ok = safe(SetBinding, key, action) end
  if ok == false then say("the game won't bind " .. keyName(key) .. "."); return false end
  safe(SaveBindings, GetCurrentBindingSet and GetCurrentBindingSet() or 1)
  say(keyName(key) .. " now " .. label .. ".")
  return true
end

-- Cat Form on G (player's choice), else Cmd+F. Binds the spell, so it works whatever slot the form has.
local function setCatKey(key, force)
  if not isKnown("Cat Form") then say("you don't have Cat Form yet (level 20 quest)."); return end
  local keys = (key and key ~= "") and { key:upper() } or { "G", "META-F" }
  for _, k in ipairs(keys) do
    if bindOne(k, "SPELL Cat Form", "turns you into Cat Form", force, "Cat Form") then
      DruidKitDB.catKeySet, DruidKitDB.catKeyBy = k, nil; askReload(); return
    end
  end
  say("type /dk catkey G force to take G, or /dk catkey <key>.")
end
DruidKit_SetCatKey = setCatKey

-- Autorun on Cmd+W (player's choice). Option+W and ` stay as spares. A double tap of W can't be a binding.
local function setRunKey(key, force)
  local k = (key and key ~= "") and key:upper() or "META-W"
  if bindOne(k, "TOGGLEAUTORUN", "toggles autorun", force) then DruidKitDB.runKeySet = k; askReload()
  else say("type /dk runkey " .. k .. " force to take it, or /dk runkey <key>. Option+W still works.") end
end
DruidKit_SetRunKey = setRunKey

function DruidKit_SetDefaultKeys()
  if InCombatLockdown() then say("after combat, please."); return end
  pcall(setDefaultGuideKey); pcall(setDefaultTabKeys); pcall(setDefaultBagsKey); pcall(setDefaultGoKey); pcall(setDefaultAutorunKey); pcall(setDefaultModeKey); pcall(setDefaultStepsKey)
  if not DruidKitDB.runKeySet then pcall(setRunKey) end
  if not DruidKitDB.catKeySet and isKnown("Cat Form") then pcall(setCatKey) end
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
  warn:SetSize(420, 40); DruidKitPos.place(warn, "warn"); warn:SetFrameStrata("HIGH")
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
