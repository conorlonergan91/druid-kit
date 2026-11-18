-- Claude Progress: snapshots your character into ClaudeProgressDB.
-- WoW writes the file to disk on /reload or logout.
-- Read-only: this addon never changes anything in game (it only reads your gear, bags and quest log).

local ADDON = "ClaudeProgress"

local function safe(fn, ...)
  local ok, a, b, c, d, e, f, g, h, i, j, k, l = pcall(fn, ...)
  if ok then return a, b, c, d, e, f, g, h, i, j, k, l end
  return nil
end

local function snapshotBasics()
  local x, y
  if C_Map and C_Map.GetBestMapForUnit then
    local mapID = safe(C_Map.GetBestMapForUnit, "player")
    if mapID then
      local pos = safe(C_Map.GetPlayerMapPosition, mapID, "player")
      if pos then
        x, y = pos.x, pos.y
        if x and y then x = math.floor(x * 1000 + 0.5) / 10; y = math.floor(y * 1000 + 0.5) / 10 end
      end
    end
  end
  local money = safe(GetMoney) or 0
  return {
    name = safe(UnitName, "player"),
    realm = safe(GetRealmName),
    class = safe(UnitClass, "player"),
    race = safe(UnitRace, "player"),
    level = safe(UnitLevel, "player"),
    xp = safe(UnitXP, "player"),
    xpMax = safe(UnitXPMax, "player"),
    rested = safe(GetXPExhaustion) or 0,
    zone = safe(GetZoneText),
    subzone = safe(GetSubZoneText),
    x = x, y = y,
    gold = math.floor(money / 10000),
    silver = math.floor((money % 10000) / 100),
    copper = money % 100,
  }
end

local function objectivesClassic(index)
  local out = {}
  local n = safe(GetNumQuestLeaderBoards, index) or 0
  for o = 1, n do
    local text, _, done = safe(GetQuestLogLeaderBoard, o, index)
    if text then table.insert(out, { text = text, done = done and true or false }) end
  end
  return out
end

local function snapshotQuests()
  local quests = {}
  -- Modern quest API
  if C_QuestLog and C_QuestLog.GetNumQuestLogEntries and C_QuestLog.GetInfo then
    local n = safe(C_QuestLog.GetNumQuestLogEntries) or 0
    local header
    for i = 1, n do
      local info = safe(C_QuestLog.GetInfo, i)
      if info then
        if info.isHeader then
          header = info.title
        elseif not info.isHidden then
          local q = { title = info.title, level = info.level, zone = header, id = info.questID, objectives = {} }
          q.complete = info.questID and safe(C_QuestLog.IsComplete, info.questID) and true or false
          local objs = info.questID and safe(C_QuestLog.GetQuestObjectives, info.questID)
          if objs then
            for _, o in ipairs(objs) do
              table.insert(q.objectives, { text = o.text, done = o.finished and true or false })
            end
          end
          table.insert(quests, q)
        end
      end
    end
    if #quests > 0 then return quests end
  end
  -- Classic quest API
  local n = safe(GetNumQuestLogEntries) or 0
  local header
  for i = 1, n do
    local title, level, _, isHeader, _, isComplete, _, questID = safe(GetQuestLogTitle, i)
    if title then
      if isHeader then
        header = title
      else
        table.insert(quests, {
          title = title, level = level, zone = header, id = questID,
          complete = (isComplete == 1 or isComplete == true),
          failed = (isComplete == -1),
          objectives = objectivesClassic(i),
        })
      end
    end
  end
  return quests
end

local function snapshotSkills()
  local skills = {}
  local n = safe(GetNumSkillLines) or 0
  for i = 1, n do
    local name, isHeader, _, rank, _, _, maxRank = safe(GetSkillLineInfo, i)
    if name and not isHeader and rank and maxRank and maxRank > 1 then
      table.insert(skills, { name = name, rank = rank, max = maxRank })
    end
  end
  if #skills == 0 and GetProfessions and GetProfessionInfo then
    local list = { safe(GetProfessions) }
    for _, idx in pairs(list) do
      if idx then
        local name, _, rank, maxRank = safe(GetProfessionInfo, idx)
        if name then table.insert(skills, { name = name, rank = rank, max = maxRank }) end
      end
    end
  end
  return skills
end

local lastGoodTalents -- cached while playing, because talent data can be empty at logout

local function talentDiagnostics()
  local d = {}
  for _, fn in ipairs({ "GetNumTalentTabs", "GetTalentTabInfo", "GetNumTalents", "GetTalentInfo",
                        "UnitCharacterPoints", "GetUnspentTalentPoints", "GetActiveTalentGroup" }) do
    d[fn] = type(_G[fn])
  end
  d.C_SpecializationInfo = type(C_SpecializationInfo)
  d.C_ClassTalents = type(C_ClassTalents)
  d.C_Traits = type(C_Traits)
  d.numTabs = safe(GetNumTalentTabs)
  d.numTabsArgs = safe(GetNumTalentTabs, false, false)
  if GetTalentTabInfo then
    local r = { safe(GetTalentTabInfo, 1) }
    d.tab1 = {}
    for i = 1, 8 do d.tab1[i] = tostring(r[i]) end
  end
  return d
end

local function readTrees(tabArgs)
  local trees, total = {}, 0
  local tabs = safe(GetNumTalentTabs, unpack(tabArgs)) or 0
  for t = 1, tabs do
    local r = { safe(GetTalentTabInfo, t) }
    -- Old clients: (name, icon, pointsSpent). Newer: (id, name, description, icon, pointsSpent, ...)
    local treeName = type(r[1]) == "string" and r[1] or r[2]
    local tree = { name = treeName, talents = {} }
    local n = safe(GetNumTalents, t) or 0
    for i = 1, n do
      local name, _, tier, column, rank, maxRank = safe(GetTalentInfo, t, i)
      if name and rank and rank > 0 then
        total = total + rank
        table.insert(tree.talents, { name = name, rank = rank, max = maxRank, tier = tier, column = column })
      end
    end
    table.insert(trees, tree)
  end
  return trees, total
end

-- Modern talent system (C_ClassTalents / C_Traits), used by WoW Forever.
local function spellNameFromDefinition(defID)
  local def = defID and safe(C_Traits.GetDefinitionInfo, defID)
  if not def then return nil end
  if def.overrideName and def.overrideName ~= "" then return def.overrideName end
  local id = def.spellID or def.overriddenSpellID
  if not id then return nil end
  return (C_Spell and C_Spell.GetSpellName and safe(C_Spell.GetSpellName, id)) or (GetSpellInfo and safe(GetSpellInfo, id))
end

local function readTraitTrees()
  if not (C_ClassTalents and C_Traits and C_ClassTalents.GetActiveConfigID) then return {}, 0, nil end
  local configID = safe(C_ClassTalents.GetActiveConfigID)
  if not configID then return {}, 0, nil end
  local config = safe(C_Traits.GetConfigInfo, configID)
  if not config or not config.treeIDs then return {}, 0, nil end
  local trees, total, unspent = {}, 0, nil
  for _, treeID in ipairs(config.treeIDs) do
    local tree = { name = "tree " .. treeID, talents = {} }
    local currencies = safe(C_Traits.GetTreeCurrencyInfo, configID, treeID, false)
    if currencies then
      for _, c in ipairs(currencies) do unspent = (unspent or 0) + (c.quantity or 0) end
    end
    for _, nodeID in ipairs(safe(C_Traits.GetTreeNodes, treeID) or {}) do
      local node = safe(C_Traits.GetNodeInfo, configID, nodeID)
      if node and (node.activeRank or 0) > 0 then
        local entryID = (node.activeEntry and node.activeEntry.entryID) or (node.entryIDs and node.entryIDs[1])
        local entry = entryID and safe(C_Traits.GetEntryInfo, configID, entryID)
        local name = entry and spellNameFromDefinition(entry.definitionID) or ("node " .. nodeID)
        total = total + node.activeRank
        table.insert(tree.talents, { name = name, rank = node.activeRank, max = node.maxRanks, row = node.posY, col = node.posX })
      end
    end
    table.insert(trees, tree)
  end
  return trees, total, unspent
end

local function snapshotTalents()
  local unspent = safe(UnitCharacterPoints, "player") or safe(GetUnspentTalentPoints)
  local trees, total = readTrees({})
  if #trees == 0 and GetNumTalentTabs then trees, total = readTrees({ false, false }) end
  if #trees == 0 then
    local u
    trees, total, u = readTraitTrees()
    unspent = unspent or u
  end
  local result = { unspent = unspent, trees = trees, pointsSpent = total }
  if #trees > 0 then
    lastGoodTalents = result
    return result
  end
  if lastGoodTalents then
    lastGoodTalents.fromCache = true
    return lastGoodTalents
  end
  result.diagnostics = talentDiagnostics()
  return result
end

local function snapshotBags()
  local free, total = 0, 0
  for bag = 0, 4 do
    local f = (C_Container and C_Container.GetContainerNumFreeSlots and safe(C_Container.GetContainerNumFreeSlots, bag))
      or (GetContainerNumFreeSlots and safe(GetContainerNumFreeSlots, bag)) or 0
    local s = (C_Container and C_Container.GetContainerNumSlots and safe(C_Container.GetContainerNumSlots, bag))
      or (GetContainerNumSlots and safe(GetContainerNumSlots, bag)) or 0
    free, total = free + (f or 0), total + (s or 0)
  end
  return { free = free, total = total }
end

local function snapshotDurability()
  local lowest, low = nil, {}
  for slot = 1, 18 do
    local cur, max = safe(GetInventoryItemDurability, slot)
    if cur and max and max > 0 then
      local pct = math.floor(cur / max * 100)
      if not lowest or pct < lowest then lowest = pct end
      if pct < 50 then
        local link = safe(GetInventoryItemLink, "player", slot)
        local name = link and link:match("%[(.-)%]") or ("slot " .. slot)
        table.insert(low, { item = name, percent = pct })
      end
    end
  end
  return lowest, low
end

-- Gear: what you wear, gear in your bags, and quest reward choices, with stats,
-- so Claude can say which reward to pick. Read-only.
local SLOT_NAMES = { [1] = "Head", [2] = "Neck", [3] = "Shoulder", [4] = "Shirt", [5] = "Chest", [6] = "Waist", [7] = "Legs",
  [8] = "Feet", [9] = "Wrist", [10] = "Hands", [11] = "Finger 1", [12] = "Finger 2", [13] = "Trinket 1", [14] = "Trinket 2",
  [15] = "Back", [16] = "Main hand", [17] = "Off hand", [18] = "Ranged", [19] = "Tabard" }
local STAT_SHORT = {
  ITEM_MOD_STRENGTH_SHORT = "Str", ITEM_MOD_AGILITY_SHORT = "Agi", ITEM_MOD_STAMINA_SHORT = "Sta",
  ITEM_MOD_INTELLECT_SHORT = "Int", ITEM_MOD_SPIRIT_SHORT = "Spi", RESISTANCE0_NAME = "Armor",
  ITEM_MOD_ATTACK_POWER_SHORT = "AP", ITEM_MOD_SPELL_POWER_SHORT = "SpellPower", ITEM_MOD_SPELL_HEALING_DONE_SHORT = "Healing",
  ITEM_MOD_CRIT_RATING_SHORT = "Crit", ITEM_MOD_HIT_RATING_SHORT = "Hit", ITEM_MOD_DEFENSE_SKILL_RATING_SHORT = "Defense",
  ITEM_MOD_DODGE_RATING_SHORT = "Dodge", ITEM_MOD_MANA_REGENERATION_SHORT = "MP5", ITEM_MOD_DAMAGE_PER_SECOND_SHORT = "DPS",
}

local function itemFacts(link)
  if not link then return nil end
  local name, _, quality, ilvl, reqLevel, itemType, subType, _, equipLoc, _, sellPrice
  if C_Item and C_Item.GetItemInfo then
    name, _, quality, ilvl, reqLevel, itemType, subType, _, equipLoc, _, sellPrice = safe(C_Item.GetItemInfo, link)
  end
  if not name and GetItemInfo then
    name, _, quality, ilvl, reqLevel, itemType, subType, _, equipLoc, _, sellPrice = safe(GetItemInfo, link)
  end
  local out = {
    name = name or link:match("%[(.-)%]"), quality = quality, itemLevel = ilvl, reqLevel = reqLevel,
    type = itemType, subType = subType, equipLoc = equipLoc, sellCopper = sellPrice,
    id = tonumber(link:match("item:(%d+)")),
  }
  local stats = (C_Item and C_Item.GetItemStats and safe(C_Item.GetItemStats, link)) or (GetItemStats and safe(GetItemStats, link))
  if type(stats) == "table" then
    local s = {}
    for k, v in pairs(stats) do
      if type(v) == "number" then s[STAT_SHORT[k] or k] = math.floor(v * 10 + 0.5) / 10 end
    end
    out.stats = s
  end
  if not name then out.notCached = true end
  return out
end

local function snapshotGear()
  local worn = {}
  for slot = 1, 19 do
    local link = safe(GetInventoryItemLink, "player", slot)
    if link then
      local f = itemFacts(link)
      if f then f.slot = SLOT_NAMES[slot]; table.insert(worn, f) end
    end
  end
  return worn
end

local function snapshotBagGear()
  local out = {}
  for bag = 0, 4 do
    local n = (C_Container and C_Container.GetContainerNumSlots and safe(C_Container.GetContainerNumSlots, bag))
      or (GetContainerNumSlots and safe(GetContainerNumSlots, bag)) or 0
    for slot = 1, n do
      local link
      if C_Container and C_Container.GetContainerItemLink then link = safe(C_Container.GetContainerItemLink, bag, slot)
      elseif GetContainerItemLink then link = safe(GetContainerItemLink, bag, slot) end
      if link then
        local f = itemFacts(link)
        if f and f.equipLoc and f.equipLoc ~= "" and f.equipLoc ~= "INVTYPE_BAG" and f.equipLoc ~= "INVTYPE_NON_EQUIP_IGNORE" and f.equipLoc ~= "INVTYPE_NON_EQUIP" then table.insert(out, f) end
      end
    end
  end
  return out
end

-- Reward choices for every quest in your log. Selecting a log entry is only to read it;
-- the previous selection is put back straight away.
local function snapshotQuestRewards()
  local out = {}
  if not (C_QuestLog and C_QuestLog.GetNumQuestLogEntries and C_QuestLog.GetInfo) then return out end
  local prev = C_QuestLog.GetSelectedQuest and safe(C_QuestLog.GetSelectedQuest)
  local n = safe(C_QuestLog.GetNumQuestLogEntries) or 0
  for i = 1, n do
    local info = safe(C_QuestLog.GetInfo, i)
    if info and not info.isHeader and info.questID then
      local qid = info.questID
      if C_QuestLog.SetSelectedQuest then safe(C_QuestLog.SetSelectedQuest, qid) end
      local entry = { title = info.title, id = qid, choices = {}, given = {} }
      local nc = (GetNumQuestLogChoices and (safe(GetNumQuestLogChoices, qid) or safe(GetNumQuestLogChoices))) or 0
      for c = 1, nc do
        local link = GetQuestLogItemLink and safe(GetQuestLogItemLink, "choice", c)
        local f = itemFacts(link)
        if f then table.insert(entry.choices, f) end
      end
      local nr = (GetNumQuestLogRewards and (safe(GetNumQuestLogRewards, qid) or safe(GetNumQuestLogRewards))) or 0
      for r = 1, nr do
        local link = GetQuestLogItemLink and safe(GetQuestLogItemLink, "reward", r)
        local f = itemFacts(link)
        if f then table.insert(entry.given, f) end
      end
      if GetQuestLogRewardMoney then entry.moneyCopper = safe(GetQuestLogRewardMoney, qid) or safe(GetQuestLogRewardMoney) end
      if GetQuestLogRewardXP then entry.xp = safe(GetQuestLogRewardXP, qid) or safe(GetQuestLogRewardXP) end
      if #entry.choices > 0 or #entry.given > 0 or entry.xp then table.insert(out, entry) end
    end
  end
  if prev and C_QuestLog.SetSelectedQuest then safe(C_QuestLog.SetSelectedQuest, prev) end
  return out
end

local BAR_BINDINGS = {
  -- slot ranges in the standard action bar layout, with the binding names that drive them
  { first = 1,   prefix = "ACTIONBUTTON",           bar = "Main bar" },
  { first = 61,  prefix = "MULTIACTIONBAR1BUTTON",  bar = "Bottom left bar" },
  { first = 49,  prefix = "MULTIACTIONBAR2BUTTON",  bar = "Bottom right bar" },
  { first = 25,  prefix = "MULTIACTIONBAR3BUTTON",  bar = "Right bar" },
  { first = 37,  prefix = "MULTIACTIONBAR4BUTTON",  bar = "Right bar 2" },
  { first = 97,  prefix = "ACTIONBUTTON",           bar = "Bear Form bar" },
  { first = 73,  prefix = "ACTIONBUTTON",           bar = "Cat Form bar" },
  { first = 85,  prefix = "ACTIONBUTTON",           bar = "Cat Form prowling bar" },
}

local function actionName(slot)
  local has
  if C_ActionBar and C_ActionBar.HasAction then has = safe(C_ActionBar.HasAction, slot) else has = HasAction and safe(HasAction, slot) end
  if not has then return nil end
  local kind, id
  if C_ActionBar and C_ActionBar.GetActionInfo then kind, id = safe(C_ActionBar.GetActionInfo, slot) end
  if not kind then kind, id = safe(GetActionInfo, slot) end
  local name
  if kind == "spell" and id then
    if C_Spell and C_Spell.GetSpellName then name = safe(C_Spell.GetSpellName, id) end
    if not name and GetSpellInfo then name = safe(GetSpellInfo, id) end
  elseif kind == "item" and id then
    if C_Item and C_Item.GetItemNameByID then name = safe(C_Item.GetItemNameByID, id) end
    if not name and GetItemInfo then name = safe(GetItemInfo, id) end
  elseif kind == "macro" and id then
    name = safe(GetMacroInfo, id)
    if name then name = "Macro: " .. name end
  end
  return name or (kind and (kind .. " " .. tostring(id))) or "?"
end

local function snapshotActionBars()
  local bars = {}
  for _, b in ipairs(BAR_BINDINGS) do
    local buttons = {}
    for i = 1, 12 do
      local slot = b.first + i - 1
      local okName, name = pcall(actionName, slot)
      if not okName then name = "error: " .. tostring(name) end
      local key = GetBindingKey and safe(GetBindingKey, b.prefix .. i)
      if name or key then
        table.insert(buttons, { button = i, slot = slot, action = name, key = key })
      end
    end
    if #buttons > 0 then table.insert(bars, { bar = b.bar, buttons = buttons }) end
  end
  local stance = {}
  for i = 1, 10 do
    -- Older clients: (icon, name, active, castable); newer: (icon, active, castable, spellID)
    local r = { safe(GetShapeshiftFormInfo, i) }
    local name = type(r[2]) == "string" and r[2] or nil
    if not name and type(r[4]) == "number" then
      name = (C_Spell and C_Spell.GetSpellName and safe(C_Spell.GetSpellName, r[4])) or (GetSpellInfo and safe(GetSpellInfo, r[4]))
    end
    local key = GetBindingKey and safe(GetBindingKey, "SHAPESHIFTBUTTON" .. i)
    if name or key then table.insert(stance, { button = i, form = name, key = key }) end
  end
  return { bars = bars, shapeshiftBar = stance }
end

-- Inventory, bank and recipes (v1.7) --------------------------------------------------------
local function cslots(bag)
  return (C_Container and C_Container.GetContainerNumSlots and safe(C_Container.GetContainerNumSlots, bag))
    or (GetContainerNumSlots and safe(GetContainerNumSlots, bag)) or 0
end
local function cinfo(bag, slot)
  if C_Container and C_Container.GetContainerItemInfo then
    local i = safe(C_Container.GetContainerItemInfo, bag, slot)
    if i then return i.hyperlink, i.stackCount or 1, i.itemID end
    return nil
  end
  if GetContainerItemInfo then
    local _, count, _, _, _, _, link = safe(GetContainerItemInfo, bag, slot)
    return link, count or 1
  end
end
local function countBags(bags)
  local out, used, total = {}, 0, 0
  for _, bag in ipairs(bags) do
    local n = cslots(bag) or 0
    total = total + n
    for slot = 1, n do
      local link, count, id = cinfo(bag, slot)
      if link then
        used = used + 1
        local name, _, q, _, _, itype, subType = safe(GetItemInfo, link)
        name = name or (link:match("%[(.-)%]")) or "?"
        local e = out[name] or { count = 0, id = id or tonumber(link:match("item:(%d+)")), quality = q, type = itype, subType = subType }
        e.count = e.count + (count or 1)
        out[name] = e
      end
    end
  end
  return out, used, total
end
local function bankBagIDs()
  local list = { (Enum and Enum.BagIndex and Enum.BagIndex.Bank) or BANK_CONTAINER or -1 }
  if Enum and Enum.BagIndex and Enum.BagIndex.CharacterBankTab_1 then
    -- Newer bank (tabs): add every tab, then the old bank bags too if they exist.
    for i = 0, 5 do local id = Enum.BagIndex.CharacterBankTab_1 + i; if id then table.insert(list, id) end end
  end
  if Enum and Enum.BagIndex and Enum.BagIndex.BankBag_1 then
    for i = 0, 6 do table.insert(list, Enum.BagIndex.BankBag_1 + i) end
  else
    local first = (NUM_BAG_SLOTS or 4) + 1
    for i = 0, (NUM_BANKBAGSLOTS or 7) - 1 do table.insert(list, first + i) end
  end
  local seen, out = {}, {}
  for _, b in ipairs(list) do if not seen[b] then seen[b] = true; table.insert(out, b) end end
  return out
end
local function charKey() return (safe(UnitName, "player") or "unknown") .. "-" .. (safe(GetRealmName) or "realm") end

local function snapshotInventory()
  local items, used, total = countBags({ 0, 1, 2, 3, 4 })
  return { items = items, used = used, total = total }
end

local bankOpen = false
local function snapshotBank()
  if not bankOpen then return end
  local items, used, total = countBags(bankBagIDs())
  if total == 0 then return end
  ClaudeProgressDB = ClaudeProgressDB or {}
  ClaudeProgressDB.bank = ClaudeProgressDB.bank or {}
  ClaudeProgressDB.bank[charKey()] = { savedAt = (date and date("%Y-%m-%d %H:%M") or ""), items = items, used = used, total = total }
end

local GATHER = { Herbalism = true, Fishing = true, Mining = true, Skinning = true }
local PROF_IDS = { [171] = "Alchemy", [129] = "First Aid", [185] = "Cooking", [356] = "Fishing", [182] = "Herbalism", [186] = "Mining", [393] = "Skinning", [197] = "Tailoring", [165] = "Leatherworking", [164] = "Blacksmithing", [202] = "Engineering", [333] = "Enchanting" }
local lastInfo
local DIFF = { [0] = "orange", [1] = "yellow", [2] = "green", [3] = "grey" }
local KIND = { optimal = "orange", medium = "yellow", easy = "green", trivial = "grey" }
local function readRecipes()
  local prof, rank, maxRank, list = nil, nil, nil, {}
  if GetNumTradeSkills and GetTradeSkillLine and GetTradeSkillInfo then
    prof, rank, maxRank = GetTradeSkillLine()
    for i = 1, (GetNumTradeSkills() or 0) do
      local name, kind, avail = GetTradeSkillInfo(i)
      if name and kind ~= "header" and kind ~= "subheader" then
        local r = { name = name, colour = KIND[kind] or kind, canMake = avail or 0, reagents = {} }
        for j = 1, (GetTradeSkillNumReagents and GetTradeSkillNumReagents(i) or 0) do
          local rn, _, need, have = GetTradeSkillReagentInfo(i, j)
          if rn then table.insert(r.reagents, { name = rn, need = need, have = have }) end
        end
        table.insert(list, r)
      end
    end
  elseif C_TradeSkillUI and C_TradeSkillUI.GetAllRecipeIDs then
    local base = C_TradeSkillUI.GetBaseProfessionInfo and safe(C_TradeSkillUI.GetBaseProfessionInfo)
    local child = C_TradeSkillUI.GetChildProfessionInfo and safe(C_TradeSkillUI.GetChildProfessionInfo)
    local function nm(i) return i and ((i.parentProfessionName ~= "" and i.parentProfessionName) or (i.professionName ~= "" and i.professionName)) or nil end
    prof = nm(base) or nm(child)
    local id = (base and (base.professionID or base.parentProfessionID)) or (child and (child.parentProfessionID or child.professionID))
    if not prof and id then prof = PROF_IDS[id] end
    if not prof and child and child.professionID then prof = PROF_IDS[child.professionID] end
    if not prof and C_TradeSkillUI.GetProfessionInfoBySkillLineID and id then
      local i2 = safe(C_TradeSkillUI.GetProfessionInfoBySkillLineID, id); prof = nm(i2)
    end
    lastInfo = { base = base and { name = base.professionName, parent = base.parentProfessionName, id = base.professionID, pid = base.parentProfessionID, lvl = base.skillLevel, max = base.maxSkillLevel } or nil,
                 child = child and { name = child.professionName, parent = child.parentProfessionName, id = child.professionID, pid = child.parentProfessionID, lvl = child.skillLevel, max = child.maxSkillLevel } or nil }
    local src = (child and child.maxSkillLevel and child.maxSkillLevel > 0) and child or base
    rank, maxRank = src and src.skillLevel, src and src.maxSkillLevel
    for _, rid in ipairs(C_TradeSkillUI.GetAllRecipeIDs() or {}) do
      local ri = safe(C_TradeSkillUI.GetRecipeInfo, rid)
      if ri and ri.learned then
        local r = { name = ri.name, colour = DIFF[ri.relativeDifficulty] or tostring(ri.relativeDifficulty), canMake = ri.numAvailable or 0, reagents = {} }
        local sch = C_TradeSkillUI.GetRecipeSchematic and safe(C_TradeSkillUI.GetRecipeSchematic, rid, false)
        for _, slot in ipairs(sch and sch.reagentSlotSchematics or {}) do
          local item = slot.reagents and slot.reagents[1] and slot.reagents[1].itemID
          if item then
            local rn = (C_Item and C_Item.GetItemNameByID and safe(C_Item.GetItemNameByID, item)) or safe(GetItemInfo, item)
            local have = (C_Item and C_Item.GetItemCount and safe(C_Item.GetItemCount, item, true)) or (GetItemCount and safe(GetItemCount, item, true))
            table.insert(r.reagents, { name = rn or ("item " .. item), id = item, need = slot.quantityRequired, have = have })
          end
        end
        table.insert(list, r)
      end
    end
  end
  return prof, rank, maxRank, list
end
local function snapshotRecipes()
  local prof1 = readRecipes()
  if not prof1 or prof1 == "" or prof1 == "UNKNOWN" or GATHER[prof1] then
    ClaudeProgressDB = ClaudeProgressDB or {}; ClaudeProgressDB.recipeDebug = lastInfo
    return
  end
  -- Read twice, half a second apart: right after switching windows the list can still be the old profession's.
  C_Timer.After(0.6, function()
    local prof, rank, maxRank, list = readRecipes()
    if prof ~= prof1 or #list == 0 then return end
    ClaudeProgressDB = ClaudeProgressDB or {}
    ClaudeProgressDB.recipes = ClaudeProgressDB.recipes or {}
    local k = charKey()
    ClaudeProgressDB.recipes[k] = ClaudeProgressDB.recipes[k] or {}
    ClaudeProgressDB.recipes[k][""] = nil
    ClaudeProgressDB.recipeDebug = lastInfo
    ClaudeProgressDB.recipes[k][prof] = { savedAt = (date and date("%Y-%m-%d %H:%M") or ""), rank = rank, max = maxRank, list = list }
  end)
end

local pf = CreateFrame("Frame")
for _, ev in ipairs({ "PLAYER_INTERACTION_MANAGER_FRAME_SHOW", "PLAYER_INTERACTION_MANAGER_FRAME_HIDE", "BANKFRAME_OPENED", "BANKFRAME_CLOSED", "PLAYERBANKSLOTS_CHANGED", "BAG_UPDATE_DELAYED", "TRADE_SKILL_SHOW", "TRADE_SKILL_LIST_UPDATE", "TRADE_SKILL_UPDATE" }) do
  pcall(pf.RegisterEvent, pf, ev)
end
local recPending
pf:SetScript("OnEvent", function(_, ev, a1)
  local BANKER = Enum and Enum.PlayerInteractionType and Enum.PlayerInteractionType.Banker or 8
  if ev == "PLAYER_INTERACTION_MANAGER_FRAME_SHOW" then
    if a1 == BANKER then bankOpen = true; C_Timer.After(0.5, function() safe(snapshotBank) end) end
  elseif ev == "PLAYER_INTERACTION_MANAGER_FRAME_HIDE" then
    if a1 == BANKER then safe(snapshotBank); bankOpen = false end
  elseif ev == "BANKFRAME_OPENED" then bankOpen = true; safe(snapshotBank)
  elseif ev == "BANKFRAME_CLOSED" then safe(snapshotBank); bankOpen = false
  elseif ev == "PLAYERBANKSLOTS_CHANGED" or ev == "BAG_UPDATE_DELAYED" then safe(snapshotBank)
  elseif not recPending then
    recPending = true
    C_Timer.After(0.3, function() recPending = false; safe(snapshotRecipes) end)
  end
end)

-- Travel (v1.9): flight paths you know (read from the flight map each time it opens; the list covers the
-- whole continent, so one visit to any flight master fills it) and where your hearthstone is set.
local function readTaxiNodes()
  local out, n = {}, 0
  local count = safe(NumTaxiNodes) or 0
  for i = 1, count do
    local kind = safe(TaxiNodeGetType, i)
    local name = safe(TaxiNodeName, i)
    if name and (kind == "CURRENT" or kind == "REACHABLE") then out[name] = true; n = n + 1 end
  end
  if n == 0 and C_TaxiMap and C_TaxiMap.GetAllTaxiNodes and C_Map and C_Map.GetBestMapForUnit then
    local nodes = safe(C_TaxiMap.GetAllTaxiNodes, safe(C_Map.GetBestMapForUnit, "player"))
    local S = Enum and Enum.FlightPathState or { Current = 0, Reachable = 1 }
    for _, nd in ipairs(nodes or {}) do
      if nd.name and (nd.state == S.Current or nd.state == S.Reachable) then out[nd.name] = true; n = n + 1 end
    end
  end
  return out, n
end

local function recordFlights()
  local nodes, n = readTaxiNodes()
  if n == 0 then return end
  ClaudeProgressDB = ClaudeProgressDB or {}
  ClaudeProgressDB.flights = ClaudeProgressDB.flights or {}
  local key = charKey()
  local known = ClaudeProgressDB.flights[key] or {}
  for name in pairs(nodes) do known[name] = true end
  ClaudeProgressDB.flights[key] = known
end

local HEARTHSTONE = 6948
local function snapshotTravel()
  local cd
  local getCd = (C_Container and C_Container.GetItemCooldown) or GetItemCooldown
  local start, dur = safe(getCd, HEARTHSTONE)
  if type(start) == "number" and type(dur) == "number" and start > 0 and GetTime then
    cd = math.max(0, math.floor(start + dur - GetTime()))
  end
  local flights = ClaudeProgressDB and ClaudeProgressDB.flights and ClaudeProgressDB.flights[charKey()]
  local list = {}
  for name in pairs(flights or {}) do table.insert(list, name) end
  table.sort(list)
  return { home = safe(GetBindLocation), hearthCooldown = cd or 0, flights = list, flightsKnown = flights ~= nil }
end

local tf = CreateFrame("Frame")
pcall(tf.RegisterEvent, tf, "TAXIMAP_OPENED")
tf:SetScript("OnEvent", function() safe(recordFlights) end)

-- Completed quests (v1.8): ids the server says are done, with titles where the client has them cached.
local function snapshotCompleted()
  local ids = (C_QuestLog and C_QuestLog.GetAllCompletedQuestIDs and C_QuestLog.GetAllCompletedQuestIDs()) or nil
  if not ids and GetQuestsCompleted then
    local t = {}; GetQuestsCompleted(t); ids = {}
    for id in pairs(t) do table.insert(ids, id) end
  end
  local out, n = {}, 0
  for _, id in ipairs(ids or {}) do
    local title = C_QuestLog and C_QuestLog.GetTitleForQuestID and safe(C_QuestLog.GetTitleForQuestID, id)
    if not title and C_QuestLog and C_QuestLog.RequestLoadQuestByID then pcall(C_QuestLog.RequestLoadQuestByID, id) end
    out[id] = title or true
    n = n + 1
  end
  return { count = n, quests = out }
end

local function hollow()
  -- While the game is quitting, XP, bags and skills read as empty. Don't save that over a good snapshot.
  local max = safe(UnitXPMax, "player")
  local bags = snapshotBags()
  return (not max or max == 0) or (not bags or (bags.total or 0) == 0)
end

local function snapshot()
  local key = (safe(UnitName, "player") or "unknown") .. "-" .. (safe(GetRealmName) or "realm")
  ClaudeProgressDB = ClaudeProgressDB or {}
  if hollow() and ClaudeProgressDB[key] then
    ClaudeProgressDB[key].lastQuit = date("%Y-%m-%d %H:%M")
    return ClaudeProgressDB[key]
  end
  ClaudeProgressDB[key] = {
    savedAt = date("%Y-%m-%d %H:%M"),
    savedTime = time(),
    basics = snapshotBasics(),
    quests = snapshotQuests(),
    skills = snapshotSkills(),
    talents = snapshotTalents(),
    bags = snapshotBags(),
  }
  local okBars, bars = pcall(snapshotActionBars)
  ClaudeProgressDB[key].actionBars = okBars and bars or { error = tostring(bars) }
  local okG, gear = pcall(snapshotGear)
  ClaudeProgressDB[key].gear = okG and gear or { error = tostring(gear) }
  local okB, bagGear = pcall(snapshotBagGear)
  ClaudeProgressDB[key].bagGear = okB and bagGear or { error = tostring(bagGear) }
  local okQ, rewards = pcall(snapshotQuestRewards)
  ClaudeProgressDB[key].questRewards = okQ and rewards or { error = tostring(rewards) }
  local okC, done = pcall(snapshotCompleted)
  ClaudeProgressDB[key].completed = okC and done or { error = tostring(done) }
  local okT, travel = pcall(snapshotTravel)
  ClaudeProgressDB[key].travel = okT and travel or { error = tostring(travel) }
  local okI, inv = pcall(snapshotInventory)
  ClaudeProgressDB[key].inventory = okI and inv or { error = tostring(inv) }
  local lowest, low = snapshotDurability()
  ClaudeProgressDB[key].lowestDurability = lowest
  ClaudeProgressDB[key].lowDurabilityItems = low
  return ClaudeProgressDB[key]
end

local f = CreateFrame("Frame")
f:RegisterEvent("PLAYER_LOGOUT")
f:RegisterEvent("PLAYER_ENTERING_WORLD")
for _, ev in ipairs({ "CHARACTER_POINTS_CHANGED", "PLAYER_TALENT_UPDATE", "PLAYER_LEVEL_UP", "SPELLS_CHANGED" }) do
  pcall(f.RegisterEvent, f, ev)
end
f:SetScript("OnEvent", function(_, event)
  if event == "PLAYER_LOGOUT" or event == "PLAYER_ENTERING_WORLD" then
    -- Login snapshot keeps the file from being empty; the logout/reload one is the fresh one.
    safe(snapshot)
  else
    -- Cache talents while playing, in case they read as empty at logout.
    safe(snapshotTalents)
  end
end)
if C_Timer and C_Timer.After then
  C_Timer.After(5, function() safe(snapshotTalents) end)
end
-- Fresh snapshot every minute while playing, so quitting with Cmd+Q still saves recent progress.
if C_Timer and C_Timer.NewTicker then
  C_Timer.NewTicker(60, function() safe(snapshot) end)
end

SLASH_CLAUDEPROGRESS1 = "/claude"
SlashCmdList["CLAUDEPROGRESS"] = function()
  local s = safe(snapshot)
  if s then
    print("|cff88ccffClaude Progress:|r snapshot taken. Type /reload to save it to disk for Claude.")
  else
    print("|cff88ccffClaude Progress:|r couldn't take a snapshot.")
  end
end
