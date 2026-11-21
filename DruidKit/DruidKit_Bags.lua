-- Druid Kit: bag check. Finds gear upgrades in your bags, junk to sell, and things to use.
--   /dk bags   open or close the Bag check panel
-- Upgrades also show a green line on the item's tooltip and a banner when you loot one.
-- At a vendor, the autopilot sells junk and gear you can't use (never potions or food); "Sell junk" sells grey only.

local GREEN, ORANGE, GREY, YELLOW = "|cff7fd35b", "|cffff7c0a", "|cff9d9d9d", "|cffffd100"
local function say(msg) print("|cff7fd35bDruid Kit:|r " .. msg) end
local function safe(fn, ...)
  if not fn then return nil end
  local ok, a, b, c, d, e, f, g, h, i, j, k, l = pcall(fn, ...)
  if ok then return a, b, c, d, e, f, g, h, i, j, k, l end
end

-- How much each stat is worth to you (bear tank + healer, levelling).
local WEIGHTS = {
  ITEM_MOD_STAMINA_SHORT = 1.0,
  ITEM_MOD_AGILITY_SHORT = 0.8,
  ITEM_MOD_STRENGTH_SHORT = 0.8,
  ITEM_MOD_INTELLECT_SHORT = 0.7,
  ITEM_MOD_SPIRIT_SHORT = 0.6,
  RESISTANCE0_NAME = 0.06,              -- armor
  ITEM_MOD_ATTACK_POWER_SHORT = 0.4,
  ITEM_MOD_SPELL_HEALING_DONE_SHORT = 0.5,
  ITEM_MOD_SPELL_POWER_SHORT = 0.5,
  ITEM_MOD_HEALTH_REGENERATION_SHORT = 1.0,
  ITEM_MOD_MANA_REGENERATION_SHORT = 1.5,
  ITEM_MOD_DAMAGE_PER_SECOND_SHORT = 1.0,   -- Forever: druid form attacks scale with weapon damage
}

-- Healing gear: Intellect, Spirit and healing power matter most.
local HEAL_WEIGHTS = {
  ITEM_MOD_INTELLECT_SHORT = 1.0,
  ITEM_MOD_SPIRIT_SHORT = 0.8,
  ITEM_MOD_STAMINA_SHORT = 0.4,
  ITEM_MOD_SPELL_HEALING_DONE_SHORT = 1.2,
  ITEM_MOD_SPELL_POWER_SHORT = 1.0,
  ITEM_MOD_MANA_REGENERATION_SHORT = 2.0,
  RESISTANCE0_NAME = 0.02,
}
local function healMode() return DruidKitDB and DruidKitDB.barMode == "heal" end
local function activeWeights() return healMode() and HEAL_WEIGHTS or WEIGHTS end
local function otherWeights() return healMode() and WEIGHTS or HEAL_WEIGHTS end

local SLOTS = {
  INVTYPE_HEAD = { 1 }, INVTYPE_NECK = { 2 }, INVTYPE_SHOULDER = { 3 }, INVTYPE_CHEST = { 5 }, INVTYPE_ROBE = { 5 },
  INVTYPE_WAIST = { 6 }, INVTYPE_LEGS = { 7 }, INVTYPE_FEET = { 8 }, INVTYPE_WRIST = { 9 }, INVTYPE_HAND = { 10 },
  INVTYPE_FINGER = { 11, 12 }, INVTYPE_TRINKET = { 13, 14 }, INVTYPE_CLOAK = { 15 },
  INVTYPE_WEAPON = { 16 }, INVTYPE_WEAPONMAINHAND = { 16 }, INVTYPE_2HWEAPON = { 16 },
  INVTYPE_HOLDABLE = { 17 }, INVTYPE_RELIC = { 18 },
}
local SLOT_NAMES = { "Head", "Neck", "Shoulders", "Shirt", "Chest", "Waist", "Legs", "Feet", "Wrists", "Hands",
  "Ring", "Ring", "Trinket", "Trinket", "Back", "Weapon", "Off-hand", "Idol" }

-- What a druid can use: cloth/leather armor, misc (rings, necks, cloaks), idols;
-- one- and two-handed maces, staves, daggers, fist weapons.
local ARMOR_OK = { [0] = true, [1] = true, [2] = true, [8] = true }   -- misc, cloth, leather, idol
local WEAPON_OK = { [4] = true, [5] = true, [6] = true, [10] = true, [13] = true, [15] = true }   -- + polearms (Forever)
-- Trade goods, reagents, quest items, recipes and containers are never junk.
local KEEP_CLASS = { [1] = true, [5] = true, [7] = true, [9] = true, [12] = true }
-- Tools are never junk either: fishing poles and miscellaneous "weapons" like mining picks.
local KEEP_WEAPON = { [14] = true, [20] = true }
-- Food/drink stacks of each kind to keep; the rest gets sold or dropped first.
local MEAL_KEEP = 2
local function isTool(classID, subID) return classID == 2 and KEEP_WEAPON[subID] end

local PROFESSIONS = { Alchemy = true, Blacksmithing = true, Enchanting = true, Engineering = true, Herbalism = true,
  Leatherworking = true, Mining = true, Skinning = true, Tailoring = true, Jewelcrafting = true, Inscription = true,
  Cooking = true, ["First Aid"] = true, Fishing = true, Lockpicking = true }
-- Recipes: what skill and rank they need, read from the item tooltip ("Requires Cooking (75)").
-- Returns the rank, false when the skill list was read and you don't have it, or nil when it can't be read.
local function readSkillLines()
  local n = GetNumSkillLines and GetSkillLineInfo and (GetNumSkillLines() or 0) or 0
  if n == 0 then return nil end
  -- Collapsed headers hide their skills: open them, read, then close them again.
  local opened, i = {}, 1
  while i <= (GetNumSkillLines() or 0) do
    local name, header, expanded = GetSkillLineInfo(i)
    if header and not expanded and ExpandSkillHeader then opened[#opened + 1] = name; ExpandSkillHeader(i) end
    i = i + 1
  end
  local ranks = {}
  for j = 1, (GetNumSkillLines() or 0) do
    local name, header, _, rank = GetSkillLineInfo(j)
    if name and not header then ranks[name] = rank or 0 end
  end
  if #opened > 0 and CollapseSkillHeader then
    local close = {}
    for _, name in ipairs(opened) do close[name] = true end
    for j = (GetNumSkillLines() or 0), 1, -1 do
      local name, header, expanded = GetSkillLineInfo(j)
      if header and expanded and close[name] then CollapseSkillHeader(j) end
    end
  end
  return ranks
end
local skillCache
local function skillRank(skill)
  if GetProfessions and GetProfessionInfo then
    for _, idx in pairs({ GetProfessions() }) do
      local name, _, rank = GetProfessionInfo(idx)
      if name == skill then return rank or 0 end
    end
    if not (GetNumSkillLines and GetSkillLineInfo) then return PROFESSIONS[skill] and false or nil end
  end
  if skillCache == nil then
    local ok, ranks = pcall(readSkillLines)
    skillCache = ok and ranks or false
  end
  if not skillCache then return nil end
  return skillCache[skill] or false
end

local scanTip
local function tooltipLines(link)
  local out = {}
  if C_TooltipInfo and C_TooltipInfo.GetHyperlink then
    local ok, data = pcall(C_TooltipInfo.GetHyperlink, link)
    if ok and data and data.lines then
      for _, l in ipairs(data.lines) do if l.leftText then table.insert(out, l.leftText) end end
      return out
    end
  end
  if not CreateFrame or not UIParent then return out end
  scanTip = scanTip or CreateFrame("GameTooltip", "DruidKitScanTip", UIParent, "GameTooltipTemplate")
  if not scanTip.SetHyperlink then return out end
  scanTip:SetOwner(UIParent, "ANCHOR_NONE"); scanTip:ClearLines(); pcall(scanTip.SetHyperlink, scanTip, link)
  for i = 1, (scanTip.NumLines and scanTip:NumLines() or 0) do
    local fs = _G["DruidKitScanTipTextLeft" .. i]
    if fs and fs.GetText then table.insert(out, fs:GetText() or "") end
  end
  return out
end

-- Can you wield it? Two checks that need no guessing (20 Nov: Smite's Mighty Hammer was called an upgrade, but the
-- player hasn't trained Two-Handed Maces):
--  1. the game's own tooltip: any line it paints red (weapon type you can't use, class, race...), except the level line;
--  2. the weapon skill's proficiency spell (Night Elf druids start with Staves and Daggers only).
local WEAPON_SKILL = { [0] = { 196, "Axes" }, [1] = { 197, "Two-Handed Axes" }, [2] = { 264, "Bows" }, [3] = { 266, "Guns" },
  [4] = { 198, "Maces" }, [5] = { 199, "Two-Handed Maces" }, [6] = { 200, "Polearms" }, [7] = { 201, "Swords" },
  [8] = { 202, "Two-Handed Swords" }, [10] = { 227, "Staves" }, [13] = { 15590, "Fist Weapons" }, [15] = { 1180, "Daggers" },
  [16] = { 2567, "Thrown" }, [18] = { 5011, "Crossbows" }, [19] = { 5009, "Wands" } }
local function knowsSpell(id)
  if IsPlayerSpell then return IsPlayerSpell(id) end
  if IsSpellKnown then return IsSpellKnown(id) end
end
local function isRed(c)
  if not c then return false end
  local r, g, b = c.r, c.g, c.b
  if c.GetRGB then r, g, b = c:GetRGB() end
  return r and r > 0.95 and g < 0.25 and b < 0.25
end
local function redLine(link)
  local levelWord = (ITEM_MIN_LEVEL and ITEM_MIN_LEVEL:match("^(%a+ %a+)")) or "Requires Level"
  if C_TooltipInfo and C_TooltipInfo.GetHyperlink then
    local ok, data = pcall(C_TooltipInfo.GetHyperlink, link)
    if ok and data and data.lines then
      for _, l in ipairs(data.lines) do
        for _, side in ipairs({ { l.leftText, l.leftColor }, { l.rightText, l.rightColor } }) do
          local txt = side[1]
          if txt and isRed(side[2]) and not txt:find(levelWord, 1, true) and not txt:find("Durability", 1, true) then return txt end
        end
      end
    end
  end
end
local function cantWield(link)
  local gi = (C_Item and C_Item.GetItemInfo) or GetItemInfo
  local _, _, _, _, _, _, _, _, equipLoc, _, _, classID, subID = gi(link)
  if classID == 2 then
    local w = WEAPON_SKILL[subID]
    if w and knowsSpell(w[1]) == false then
      return ("you haven't learned %s (a weapon master in a capital teaches it)"):format(w[2])
    end
  end
  if equipLoc and equipLoc ~= "" then
    local red = redLine(link)
    if red then return "you can't use this (" .. red .. ")" end
  end
end
DruidKit_CantWield = function(link) local ok, why = pcall(cantWield, link); if ok then return why end end

-- Who an item is for, from its tooltip: "Classes: Rogue" (not a druid's) or "Requires Engineering (100)" (a
-- profession you don't have, or not high enough). Returns a reason, or nil when you can use it.
local function restrictionNow(link)
  local wield = cantWield(link)
  if wield then return wield end
  local classLabel = (ITEM_CLASSES_ALLOWED and ITEM_CLASSES_ALLOWED:match("^([^:]+)")) or "Classes"
  local me = (UnitClass and UnitClass("player")) or "Druid"
  for _, t in ipairs(tooltipLines(link)) do
    local classes = t:match("^" .. classLabel .. ": (.+)$")
    if classes and not classes:find(me, 1, true) then return "for " .. classes .. " only" end
    if t:find("Comprehension", 1, true) and me ~= "Mage" then
      return "mage scroll (needs Comprehension): sell it, or list it on the Auction House for a mage"
    end
    local sk, n = t:match("^Requires ([%a' ]+) %((%d+)%)")
    if sk then
      local have = skillRank(sk)
      if have == false then return "needs " .. sk .. ", which you don't have" end
      if have and have < tonumber(n) and PROFESSIONS[sk] then return ("needs %s %s (you're %d)"):format(sk, n, have) end
    end
  end
end
local restrictCache = {}
local function restriction(link)
  local r = restrictCache[link]
  if r == nil then r = restrictionNow(link) or false; restrictCache[link] = r end
  return r or nil
end

-- Extra words for the sell list: Bind on Equip greens and better often fetch more on the Auction House.
local function boeHint(link, q)
  if (q or 0) < 2 then return "" end
  for _, t in ipairs(tooltipLines(link)) do
    if t == (ITEM_BIND_ON_EQUIP or "Binds when equipped") then return " (binds when equipped: may sell for more on the Auction House)" end
  end
  return ""
end
DruidKit_ItemRestriction = function(link) local ok, why = pcall(restriction, link); if ok then return why end end

-- verdict for a recipe: "learn" | "later" | "known" | "noskill" | "unknown" (skill list unreadable), plus skill, needed, have
local function recipeCheck(link)
  local skill, need, known
  for _, t in ipairs(tooltipLines(link)) do
    local sk, n = t:match("^Requires ([%a ]+) %((%d+)%)")
    if sk and not skill then skill, need = sk, tonumber(n) end
    if t == ITEM_SPELL_KNOWN or t == "Already known" then known = true end
  end
  if known then return "known" end
  local why = restriction(link)
  if why and not why:find("you're", 1, true) then return "noclass", why end   -- other class, mage scroll, no skill
  if not skill then return "learn" end
  local have = skillRank(skill)
  if have == nil then return "unknown", skill, need end
  if not have then return "noskill", skill, need end
  if have < need then return "later", skill, need, have end
  return "learn", skill, need, have
end
DruidKit_RecipeCheck = recipeCheck

local function getInfo(item)
  if C_Item and C_Item.GetItemInfo then return C_Item.GetItemInfo(item) end
  return GetItemInfo(item)
end
local function getStats(link)
  if C_Item and C_Item.GetItemStats then return C_Item.GetItemStats(link) end
  if GetItemStats then return GetItemStats(link) end
end
local function numSlots(bag)
  if C_Container and C_Container.GetContainerNumSlots then return C_Container.GetContainerNumSlots(bag) end
  return GetContainerNumSlots(bag)
end

-- Bags: how many slots a bag item has ("10 Slot Bag"), and your smallest equipped bag.
local function bagItemSlots(link)
  for _, t in ipairs(tooltipLines(link)) do
    local n = t:match("^(%d+) Slot") or t:match("(%d+) Slot Bag")
    if n then return tonumber(n) end
  end
end
local function smallestBag()
  local small, which
  for bag = 1, 4 do
    local n = numSlots(bag) or 0
    if not small or n < small then small, which = n, bag end
  end
  return small or 0, which
end
local function slotInfo(bag, slot)
  if C_Container and C_Container.GetContainerItemInfo then
    local i = C_Container.GetContainerItemInfo(bag, slot)
    if i then return i.hyperlink, i.stackCount, i.quality, i.hasLoot, i.itemID, i.isLocked end
    return
  end
  local _, count, locked, quality, _, lootable, link, _, _, id = GetContainerItemInfo(bag, slot)
  return link, count, quality, lootable, id, locked
end
local function questInfo(bag, slot)
  if C_Container and C_Container.GetContainerItemQuestInfo then
    local q = C_Container.GetContainerItemQuestInfo(bag, slot)
    if q then return q.isQuestItem, q.questID, q.isActive end
  elseif GetContainerItemQuestInfo then
    return GetContainerItemQuestInfo(bag, slot)
  end
end

-- Names of items your active quests ask for ("0/5 Strider Meat" -> "Strider Meat"). Never sell, drop or bank these.
local questNeed, questNeedAt = {}, -100
local function questItems()
  if GetTime() - questNeedAt < 3 then return questNeed end
  questNeedAt = GetTime()
  local set = {}
  local function add(text)
    local name = text and (text:match("^%d+/%d+ (.+)$") or text:match("^(.-): %d+/%d+$"))
    if name then set[name] = true end
  end
  if C_QuestLog and C_QuestLog.GetNumQuestLogEntries and C_QuestLog.GetQuestObjectives then
    for i = 1, (C_QuestLog.GetNumQuestLogEntries() or 0) do
      local q = C_QuestLog.GetInfo(i)
      if q and not q.isHeader and q.questID then
        for _, o in ipairs(C_QuestLog.GetQuestObjectives(q.questID) or {}) do add(o.text) end
      end
    end
  elseif GetNumQuestLogEntries and GetQuestLogLeaderBoard then
    for i = 1, (GetNumQuestLogEntries() or 0) do
      for j = 1, (GetNumQuestLeaderBoards(i) or 0) do add((GetQuestLogLeaderBoard(j, i))) end
    end
  end
  questNeed = set
  return set
end
DruidKit_QuestItems = function() local ok, r = pcall(questItems); return ok and r or {} end

-- Everything your quests and the route say, in lower case: titles, objective lines (delivery quests carry their
-- whole sentence there: "take the strange smelling powder to ..."), and the route's step texts. A quest item whose
-- name appears nowhere in it belongs to no quest you have.
local blob, blobAt = "", -10
local function questBlob()
  if GetTime() - blobAt < 3 then return blob end
  blobAt = GetTime()
  local parts = {}
  if C_QuestLog and C_QuestLog.GetNumQuestLogEntries and C_QuestLog.GetInfo then
    for i = 1, (C_QuestLog.GetNumQuestLogEntries() or 0) do
      local q = C_QuestLog.GetInfo(i)
      if q and not q.isHeader then
        table.insert(parts, q.title or "")
        for _, o in ipairs((q.questID and C_QuestLog.GetQuestObjectives and C_QuestLog.GetQuestObjectives(q.questID)) or {}) do
          table.insert(parts, o.text or "")
        end
      end
    end
  end
  local route = DruidKitRoute
  for _, sec in ipairs((route and route.sections) or {}) do
    for _, st in ipairs(sec.steps or {}) do
      table.insert(parts, (st.name or "") .. " " .. (st.text or "") .. " " .. (st.how or "") .. " " .. (st.tip or ""))
    end
  end
  blob = table.concat(parts, " | "):lower()
  return blob
end
-- Which quest in your log an item belongs to (its name in that quest's title or objective lines).
local function questFor(name)
  if not (name and C_QuestLog and C_QuestLog.GetNumQuestLogEntries and C_QuestLog.GetInfo) then return end
  local n = name:lower()
  for i = 1, (C_QuestLog.GetNumQuestLogEntries() or 0) do
    local q = C_QuestLog.GetInfo(i)
    if q and not q.isHeader and q.questID then
      local text = (q.title or ""):lower()
      for _, o in ipairs((C_QuestLog.GetQuestObjectives and C_QuestLog.GetQuestObjectives(q.questID)) or {}) do
        text = text .. " | " .. (o.text or ""):lower()
      end
      if text:find(n, 1, true) or text:find((n:gsub("s$", "")), 1, true) then return q.questID, q.title end
    end
  end
end

-- A quest item you won't need for a while: the update's plan (DruidKitRoute.items) says bank or drop it; without a
-- plan, bank it when the route passes a bank within ~30 steps and the quest isn't in the route at all.
local function laterPlan(name, qid, qtitle)
  local plan = DruidKitRoute and DruidKitRoute.items and DruidKitRoute.items[name]
  if plan and plan.action ~= "keep" then return plan.action, plan.why end
  if plan then return nil end
  if not (qid and DruidKit_StepsAhead and DruidKit_NextBank) then return nil end
  local ahead = DruidKit_StepsAhead(qid)
  if ahead then return nil end    -- the route still does this quest: keep it (no way to know you'll pass a bank again)
  local bank = DruidKit_NextBank(30)
  if not bank then return nil end
  return "bank", ("needed later for %s (not in your current route); bank it in %s (in about %d steps)"):format(
    qtitle or "a quest", bank.where, bank.steps)
end

DruidKit_BankLater = function(name)
  local ok, action, why = pcall(function() local qid, qt = questFor(name); return laterPlan(name, qid, qt) end)
  if ok and action == "bank" then return why end
end

local function questMentions(name)
  if not name then return false end
  local b = questBlob()
  local n = name:lower()
  return b:find(n, 1, true) ~= nil or b:find((n:gsub("s$", "")), 1, true) ~= nil
end

-- Library books (Forever): hand in to Garion Wendell, top of the Wizard's Sanctum, Stormwind Mage Quarter.
-- Never sell or destroy: a deleted book may not be lootable again.
local BOOKS = {}
for _, n in ipairs({
  "Archmage Theocritus' Research Journal", "Archmage Theocritus's Research Journal", "Archmage Antonidas: The Unabridged Autobiography",
  "The Apothecary's Metaphysical Primer", "Ataeric: On Arcane Curiosities", "The Dalaran Digest, Vol. 23",
  "Rumi of Gnomeregan: The Collected Works", "Runes of the Sorcerer-Kings", "Bewitchments and Glamours",
  "Crimes Against Anatomy", "Goaz Scrolls", "Defensive Magics 101", "A Web of Lies: Debunking Myths and Legends",
  "Basilisks: Should Petrification be Feared?", "Mummies: A Guide to the Unsavory Undead",
  "A Luddite's Guide to Caring for Your Demonic Pet", "Sanguine Sorcery", "Venomous Journeys", "A Mind of Metal",
  "Conjurer's Codex", "Stonewrought Design", "Magma or Lava?", "Necromancy 101", "Undead Potatoes",
  "A Study of the Light", "Scourge: Undead Menace or Misunderstood?", "The Knight and the Lady", "The Lessons of Ta'zo",
  "Nar'thalas Almanac, Vol. 74", "Arcanic Systems Manual", "Baxtan: On Destructive Magics", "Secrets of the Dreamers",
  "Fury of the Land", "Geomancy: The Stone-Cold Truth", "Demons and You", "RwlRwlRwlRwl!", "Legends of the Tidesages",
  "Everyday Etiquette", "Northern Kalimdor - A Comprehensive Guide", "Northern Kalimdor – A Comprehensive Guide",
  "Ka-Boom!", "Temptation and Seduction" }) do BOOKS[n] = true end
local function isBook(name) return name and BOOKS[name] or false end
DruidKit_IsLibraryBook = isBook

-- "Red Leather Bandanas" and "Red Leather Bandana" are the same thing.
local function norm(n) n = n:lower():gsub("^%s+", ""):gsub("%s+$", ""); return (n:gsub("es$", ""):gsub("s$", "")) end
local function questNeeds(name)
  if not name then return false end
  local ok, set = pcall(questItems)
  if not ok or not set then return false end
  if set[name] then return true end
  local n = norm(name)
  for k in pairs(set) do if norm(k) == n then return true end end
  return false
end

-- One check for everything that must never be sold, dropped or offered: returns a reason, or nil.
local ORPHAN = "quest item that may belong to no quest in your log"
local function protectedReason(link, bag, slot)
  local name, _, _, _, _, _, _, _, _, _, _, classID, _, bindType = getInfo(link)
  if questNeeds(name) then return "your quest needs this" end
  if isBook(name) then return "library book: hand it in at the Stormwind library" end
  if name and name:find("Waylaid") then return "Waylaid Crate" end
  local isQuestFlag, starterID = false, nil
  if bag and slot then isQuestFlag, starterID = questInfo(bag, slot) end
  if classID == 12 or bindType == 4 or isQuestFlag then
    if starterID then return nil end                 -- quest starters: handled in the scan
    if questMentions(name) then return "quest item" end
    if name and name:find("Hearthstone") then return "your hearthstone" end
    return ORPHAN                                    -- only a guess: shown to check, never offered
  end
end
DruidKit_Protected = function(link, bag, slot) local ok, r = pcall(protectedReason, link, bag, slot); return ok and r or nil end

local function usable(classID, subID, equipLoc)
  if not SLOTS[equipLoc] then return false end
  if classID == 4 then return ARMOR_OK[subID] or false end
  if classID == 2 then return WEAPON_OK[subID] or false end
  return false
end

local function score(link, w)
  local stats = safe(getStats, link)
  if not stats then return 0 end
  w = w or activeWeights()
  local s = 0
  for k, v in pairs(stats) do s = s + (w[k] or 0) * v end
  return s
end

local function equippedScore(slot, w)
  local link = GetInventoryItemLink("player", slot)
  return link and score(link, w) or 0, link
end

-- Gear sets saved with /dk healset and /dk questset: which set (if any) an item belongs to.
local function itemID(link) return link and tonumber(link:match("item:(%d+)")) end
local function setOf(link)
  local id = itemID(link)
  local sets = DruidKitDB and DruidKitDB.gearSets
  if not (id and sets) then return end
  for mode, set in pairs(sets) do
    for _, l in pairs(set) do if itemID(l) == id then return mode end end
  end
end

-- Returns gain, slot name for an item, or nil if it isn't an upgrade.
local function upgradeFor(link, w, anyLevel)
  local _, _, _, _, minLevel, _, _, _, equipLoc, _, _, classID, subID = getInfo(link)
  if not equipLoc or not usable(classID, subID, equipLoc) then return end
  if not anyLevel and (minLevel or 0) > UnitLevel("player") then return end
  if restriction(link) then return end
  local mine = score(link, w)
  if mine <= 0 then return end
  local slots = SLOTS[equipLoc]
  local current
  if equipLoc == "INVTYPE_2HWEAPON" then
    current = equippedScore(16, w) + equippedScore(17, w)
  elseif equipLoc == "INVTYPE_HOLDABLE" then
    local mh = GetInventoryItemLink("player", 16)
    local mhLoc = mh and select(9, getInfo(mh))
    if mhLoc == "INVTYPE_2HWEAPON" then return end      -- would drop your staff
    current = equippedScore(17, w)
  else
    current = math.huge
    for _, s in ipairs(slots) do current = math.min(current, (equippedScore(s, w))) end
  end
  local gain = mine - current
  if gain >= 1 then return gain, SLOT_NAMES[slots[1]], mine end
end

-- Gear worth keeping even though it isn't an upgrade right now: your saved sets, or
-- pieces that are better for your other role (healing while you quest, or the reverse).
-- Returns a reason and which role it's for ("heal" or "quest").
local function keepReason(link)
  local set = setOf(link)
  if set then return (set == "heal" and "in your healing set" or "in your questing set"), set end
  local gain, slotName = upgradeFor(link, otherWeights())
  if gain and gain >= 2 then
    local role = healMode() and "quest" or "heal"
    return ("better for %s (+%d %s)"):format(role == "heal" and "healing" or "bear", math.floor(gain + 0.5), slotName:lower()), role
  end
end
-- Quest reward choice when the route names none: the biggest upgrade for your active role, else the one that sells
-- for the most. Returns index, reason.
local function rewardPick(n)
  local best, bestGain, bestPrice, cash = nil, 0, -1, nil
  for i = 1, n do
    local link = GetQuestItemLink and GetQuestItemLink("choice", i)
    if link then
      local gain = upgradeFor(link, nil, true)
      if gain and gain > bestGain then best, bestGain = i, gain end
      local price = select(11, getInfo(link)) or 0
      if price > bestPrice then cash, bestPrice = i, price end
    end
  end
  if best then return best, "best upgrade for you" end
  if cash then return cash, "no upgrade, so the one that sells for the most" end
end
DruidKit_RewardPick = function(n) local ok, i, why = pcall(rewardPick, n); if ok then return i, why end end

DruidKit_GearKeep = function(link) local ok, a, b = pcall(keepReason, link); if ok then return a, b end end

-- Scan ------------------------------------------------------------------------------
local results = { upgrades = {}, junk = {}, unusable = {}, use = {}, junkValue = 0 }

-- Auction House price from Auctionator (installed), or nil when it has no price for the item.
local function ahPrice(link)
  local api = Auctionator and Auctionator.API and Auctionator.API.v1
  if not (api and api.GetAuctionPriceByItemLink and link) then return end
  local ok, p = pcall(api.GetAuctionPriceByItemLink, "DruidKit", link)
  if ok and type(p) == "number" and p > 0 then return p end
end
DruidKit_AHPrice = ahPrice

local function wellFed(link)
  for _, t in ipairs(tooltipLines(link) or {}) do
    local l = t:lower()
    if l:find("well fed") or l:find("experience") then return true end
  end
  return false
end

local function scanNow()
  local up, junk, unusable, use, poles, spare, kept, bank, check = {}, {}, {}, {}, {}, {}, {}, {}, {}
  local starterSeen = {}
  local meals = { Food = {}, Drink = {} }
  local junkValue = 0
  for bag = 0, 4 do
    for slot = 1, (numSlots(bag) or 0) do
      local link, count, quality, lootable, itemID = slotInfo(bag, slot)
      if link then
        local name, _, q, _, minLevel, _, _, _, equipLoc, icon, price, classID, subID = getInfo(link)
        q = q or quality
        local isQuest, questID, active = questInfo(bag, slot)
        local guard = name and protectedReason(link, bag, slot)
        if guard then
          -- quest items, library books and Waylaid Crates: never sold or dropped (but a quest item needed much later
          -- can go to the bank; one the plan says to drop, or that may belong to no quest, is shown to check)
          local e = { bag = bag, slot = slot, link = link, name = name, icon = icon, count = count or 1 }
          if isBook(name) then
            e.why = "library book: hand in to Garion Wendell (Stormwind library) or bank it"
            table.insert(bank, e)
          elseif guard == ORPHAN then
            e.why = "check: may belong to no quest in your log (abandoned or done?)"
            table.insert(check, e)
          elseif guard == "quest item" or guard == "your quest needs this" then
            local qid, qtitle = questFor(name)
            local action, why = laterPlan(name, qid, qtitle)
            e.why = why
            if action == "bank" then table.insert(bank, e)
            elseif action == "drop" then table.insert(check, e) end
          end
        elseif name then
          local entry = { bag = bag, slot = slot, link = link, name = name, icon = icon, count = count or 1 }
          local limit = (classID ~= 4 and classID ~= 2 and classID ~= 9) and restriction(link)
          local doneQ = questID and ((C_QuestLog and C_QuestLog.IsQuestFlaggedCompleted
            and C_QuestLog.IsQuestFlaggedCompleted(questID)) or (IsQuestFlaggedCompleted and IsQuestFlaggedCompleted(questID)))
          if questID and doneQ then
            entry.why, entry.value = "starts a quest you've already done: destroy it", (price or 0) * (count or 1)
            table.insert(unusable, entry)
          elseif questID and not active and laterPlan(name, nil, nil) then
            local action, why = laterPlan(name, nil, nil)
            entry.why, entry.value = why, 0
            table.insert(action == "bank" and bank or unusable, entry)
          elseif questID and not active then
            if not starterSeen[questID] then
              starterSeen[questID] = entry
              entry.why = "starts a quest: open your bags and right-click it"
              table.insert(use, entry)
            else
              local first = starterSeen[questID]
              first.copies = (first.copies or 1) + (count or 1)
              first.why = ("starts a quest: right-click one (you have %d; check the quest log after)"):format(first.copies)
            end
          elseif limit then
            -- Another class's book or scroll, another profession's item: sell, never "use" or "learn".
            entry.why, entry.value = limit, (price or 0) * (count or 1)
            table.insert(unusable, entry)
          elseif classID == 1 and (subID or 0) == 0 and bagItemSlots(link) then
            local have, small = bagItemSlots(link), smallestBag()
            entry.value = (price or 0) * (count or 1)
            if small == 0 then
              entry.why = ("bag: you have an empty bag slot, so this adds %d slots. Drag it onto the bag bar."):format(have)
              table.insert(use, entry)
            elseif have > small then
              entry.why = ("bag: %d slots, more than your %d-slot bag. Empty that bag, then swap them."):format(have, small)
              table.insert(use, entry)
            else
              entry.why = ("%d-slot bag: no bigger than the bags you use"):format(have)
              table.insert(unusable, entry)
            end
          elseif lootable then
            entry.why = "has loot inside: right-click to open"
            table.insert(use, entry)
          elseif q == 0 and (price or 0) > 0 then
            junkValue = junkValue + price * (count or 1)
            entry.value = price * (count or 1)
            table.insert(junk, entry)
          elseif classID == 2 and subID == 20 then
            entry.ilvl, entry.price = select(4, getInfo(link)) or 0, price or 0
            table.insert(poles, entry)
          elseif classID == 0 and subID == 5 and not isQuest and wellFed(link) then
            -- Cooked food with Well Fed: the +5% kill XP buff in Forever. Always keep it.
            entry.why = "cooked food: eat it for the Well Fed +5% XP buff"
            table.insert(kept, entry)
          elseif classID == 0 and subID == 5 and not isQuest then
            -- Food and drink: keep only your best stacks (sorted after the scan)
            local spell = GetItemSpell and GetItemSpell(link)
            local kind = (spell == "Drink") and "Drink" or "Food"
            entry.minLevel, entry.value = minLevel or 0, (price or 0) * (count or 1)
            table.insert(meals[kind], entry)
          elseif classID == 9 then
            local verdict, skill, need, have = recipeCheck(link)
            entry.value = (price or 0) * (count or 1)
            if verdict == "known" then
              entry.why = "you already know this recipe"
              table.insert(unusable, entry)
            elseif verdict == "noclass" then
              entry.why = skill   -- "for Rogue only"
              table.insert(unusable, entry)
            elseif verdict == "noskill" then
              entry.why = ("needs %s, which you don't have"):format(skill)
              table.insert(unusable, entry)
            elseif verdict == "later" then
              entry.why = ("learn at %s %d (you're %d): bank it till then"):format(skill, need, have)
              table.insert(bank, entry)
            elseif verdict ~= "unknown" then
              entry.why = "recipe: right-click to learn it"
              table.insert(use, entry)
            end
          elseif not isQuest and (classID == 7 or classID == 5) and DruidKit_NeededFor then
            -- Never herbs (they're for Alchemy), and nothing any recipe you know uses.
            local _, known, used = DruidKit_NeededFor(name)
            if known and not used and not (classID == 7 and subID == 9) then
              entry.why, entry.value = "none of your recipes use this", (price or 0) * (count or 1)
              table.insert(spare, entry)
            end
          elseif not isQuest and not KEEP_CLASS[classID] and not isTool(classID, subID) then
            local gain, slotName = upgradeFor(link)
            local keepWhy = SLOTS[equipLoc] and keepReason(link)
            if gain and not setOf(link) then
              entry.gain, entry.slotName = gain, slotName
              table.insert(up, entry)
            elseif keepWhy then
              entry.why = keepWhy
              table.insert(kept, entry)
            elseif SLOTS[equipLoc] and (price or 0) > 0 then
              entry.value = (price or 0) * (count or 1)
              local why = restriction(link)
              if not usable(classID, subID, equipLoc) or why then
                entry.why = (why or "druids can't use this") .. boeHint(link, q)
                table.insert(unusable, entry)
              elseif (minLevel or 0) <= UnitLevel("player") then
                entry.why = "worse than what you're wearing" .. boeHint(link, q)
                table.insert(unusable, entry)
              else
                local later, laterSlot = upgradeFor(link, nil, true)
                if later then
                  entry.why = ("for your %s at level %d: bank it till then"):format(laterSlot:lower(), minLevel)
                  table.insert(bank, entry)
                end
              end
            end
          end
        end
      end
    end
  end
  -- Keep your best fishing pole (worn or in bags); offer the others for sale.
  local worn = GetInventoryItemLink("player", 16)
  local bestIlvl, bestPrice = -1, -1
  if worn then
    local _, _, _, il, _, _, _, _, _, _, pr, c, sc = getInfo(worn)
    if c == 2 and sc == 20 then bestIlvl, bestPrice = il or 0, pr or 0 end
  end
  local best
  for _, e in ipairs(poles) do
    if e.ilvl > bestIlvl or (e.ilvl == bestIlvl and e.price > bestPrice) then best, bestIlvl, bestPrice = e, e.ilvl, e.price end
  end
  for _, e in ipairs(poles) do
    if e ~= best and e.price > 0 then e.why = "you have a better fishing pole"; e.value = e.price; table.insert(unusable, e) end
  end

  table.sort(up, function(a, b) return a.gain > b.gain end)

  -- Food and drink: keep the best MEAL_KEEP stacks of each you can use now (plus one stack for later);
  -- everything else is spare: sell it at a vendor or drop it for loot.
  local lvl = UnitLevel("player")
  for kind, list in pairs(meals) do
    table.sort(list, function(a, b)
      local au, bu = a.minLevel <= lvl, b.minLevel <= lvl
      if au ~= bu then return au end
      if a.minLevel ~= b.minLevel then return a.minLevel > b.minLevel end
      return (a.count or 1) > (b.count or 1)
    end)
    -- Count by item, not by stack: 20 + 8 Ice Cold Milk is one drink you keep all of (21 Nov: it said drop the
    -- milk just bought for the dungeon).
    local keptNow, keptLater, best = 0, 0, nil
    local keepName = {}
    for _, e in ipairs(list) do
      if keepName[e.name] then
        -- another stack of an item you keep
      elseif e.minLevel > lvl and keptLater < 1 then
        keptLater = keptLater + 1; keepName[e.name] = true
      elseif e.minLevel <= lvl and keptNow < MEAL_KEEP then
        keptNow = keptNow + 1; keepName[e.name] = true
        best = best or e
      else
        e.why = ("spare %s: you're keeping %s"):format(kind:lower(), best and best.name or "better ones")
        table.insert(unusable, e)
      end
    end
  end

  -- Make room: cheapest junk first, then gear you'd sell anyway, then spare materials.
  local drop = {}
  local function add(list, why)
    table.sort(list, function(a, b) return (a.value or 0) < (b.value or 0) end)
    for _, e in ipairs(list) do
      table.insert(drop, { bag = e.bag, slot = e.slot, link = e.link, name = e.name, icon = e.icon, count = e.count,
        value = e.value or 0, why = why or e.why })
    end
  end
  -- Auction House: anything you'd sell or drop that Auctionator's last scan prices well above the vendor
  -- (after the 5% cut). Bind on Pickup and quest items can't be listed.
  local auction = {}
  local function moveToAuction(list)
    for i = #list, 1, -1 do
      local e = list[i]
      local ah = ahPrice(e.link)
      local _, _, _, _, _, _, _, _, _, _, vend, _, _, bindType = getInfo(e.link)
      vend = vend or 0
      if ah and bindType ~= 1 and bindType ~= 4 and ah * 0.95 >= math.max(vend * 2, vend + 100) then
        e.ah, e.vendor = ah, vend
        table.insert(auction, e)
        table.remove(list, i)
      end
    end
  end
  moveToAuction(unusable)
  moveToAuction(spare)
  table.sort(auction, function(a, b) return (a.ah or 0) * (a.count or 1) > (b.ah or 0) * (b.count or 1) end)

  add(junk, "grey junk")
  for _, e in ipairs(unusable) do e.value = e.value or 0 end
  add(unusable)
  add(spare)
  add(auction, "worth more at the Auction House: drop it last")
  results = { upgrades = up, junk = junk, unusable = unusable, use = use, junkValue = junkValue, drop = drop, kept = kept,
    bank = bank, auction = auction, spare = spare, check = check }
  return results
end
local scanDirty = true
local function invalidate() scanDirty, skillCache, restrictCache = true, nil, {} end
local function scan()
  if scanDirty then scanNow(); scanDirty = false end
  return results
end

-- Panel -------------------------------------------------------------------------------
local panel
local refresh
local S

local function money(c)
  if GetCoinTextureString then return GetCoinTextureString(c) end
  return ("%dg %ds %dc"):format(c / 10000, (c / 100) % 100, c % 100)
end

local function qualityOf(link)
  local _, _, q = getInfo(link)
  return q or 1
end

local function freeSlots()
  local free, total = 0, 0
  for bag = 0, 4 do
    local n = numSlots(bag) or 0
    total = total + n
    for slot = 1, n do if not slotInfo(bag, slot) then free = free + 1 end end
  end
  return free, total
end

local function useSlot(bag, slot)
  if C_Container and C_Container.UseContainerItem then C_Container.UseContainerItem(bag, slot) else UseContainerItem(bag, slot) end
end

local function logSale(name, count, why)
  if not DruidKitDB then return end
  DruidKitDB.soldLog = DruidKitDB.soldLog or {}
  table.insert(DruidKitDB.soldLog, { name = name, count = count or 1, why = why, at = date and date("%Y-%m-%d %H:%M") })
  while #DruidKitDB.soldLog > 60 do table.remove(DruidKitDB.soldLog, 1) end
end

-- The vendor's Buyback tab holds the last 12 items: autopilot and manual sells share that cap per visit.
local BUYBACK = 12
local soldThisVisit = 0
local function buybackLeft() return BUYBACK - soldThisVisit end
local function sayMoreToSell(n)
  if n > 0 then
    say(("%d more to sell: close the vendor and talk to it again (Buyback only holds %d)."):format(n, BUYBACK))
  else
    say(("Buyback is full (%d this visit): close the vendor and talk to it again to sell more."):format(BUYBACK))
  end
end

local sellJunk
-- Sell one bag slot at an open vendor, only if it still holds the same item we listed.
local function sellEntry(e)
  if not (MerchantFrame and MerchantFrame:IsShown()) then say("talk to a vendor first.") return false end
  if buybackLeft() <= 0 then return false, "full" end
  local link = slotInfo(e.bag, e.slot)
  if link ~= e.link or protectedReason(link, e.bag, e.slot) then return false end
  useSlot(e.bag, e.slot)
  soldThisVisit = soldThisVisit + 1
  return true
end
local function sellOne(e, left)
  local _, why = sellEntry(e)
  if why == "full" then sayMoreToSell(left or 0) end
  C_Timer.After(0.4, refresh)
end

local autoSellList   -- defined with the vendor autopilot below
refresh = function()
  if not panel or not panel:IsShown() then return end
  local r = scan()
  local free, total = freeSlots()
  panel.sub:SetText(("%d of %d bag slots free"):format(free, total))
  S.begin(panel)

  S.header(panel, "Upgrades to put on", "Interface\\Icons\\INV_Chest_Leather_04", #r.upgrades)
  if #r.upgrades == 0 then S.note(panel, "Nothing better in your bags. You're wearing your best.") end
  for _, e in ipairs(r.upgrades) do
    S.item(panel, e.link, e.icon, qualityOf(e.link), e.name,
      ("|cff7fd35b+%d|r for your %s"):format(math.floor(e.gain + 0.5), e.slotName:lower()), "Equip", function()
        if InCombatLockdown() then say("can't change gear in combat.") return end
        if C_Item and C_Item.EquipItemByName then C_Item.EquipItemByName(e.link) else EquipItemByName(e.link) end
        C_Timer.After(0.5, refresh)
      end)
  end

  if #r.use > 0 then
    S.header(panel, "Use these", "Interface\\Icons\\INV_Misc_Note_01", #r.use)
    for _, e in ipairs(r.use) do
      S.item(panel, e.link, e.icon, qualityOf(e.link), e.name, (e.why:gsub("^%l", string.upper)))
    end
  end

  if #r.kept > 0 then
    S.header(panel, "Gear you're keeping", "Interface\\Icons\\INV_Misc_Bag_10_Green", #r.kept)
    S.note(panel, healMode() and "Healing mode is on. Bear and questing pieces are kept; Bank check offers to store them."
      or "Kept for healing. Bank check offers to store them while you quest. /dk heal to wear your healing set.")
    for _, e in ipairs(r.kept) do
      S.item(panel, e.link, e.icon, qualityOf(e.link), e.name, (e.why:gsub("^%l", string.upper)))
    end
  end

  if #r.bank > 0 then
    S.header(panel, "Bank these (not needed yet)", "Interface\\Icons\\INV_Box_02", #r.bank)
    S.note(panel, "Keep them, but they don't need a bag slot now. Bank check stores them at any banker.")
    for _, e in ipairs(r.bank) do
      S.item(panel, e.link, e.icon, qualityOf(e.link), e.name, (e.why:gsub("^%l", string.upper)))
    end
  end

  if r.check and #r.check > 0 then
    S.header(panel, "Quest items to check", "Interface\\Icons\\INV_Misc_Note_02", #r.check)
    S.note(panel, "Never sold or destroyed for you: check your quest log, then destroy them yourself if they're done with.")
    for _, e in ipairs(r.check) do
      S.item(panel, e.link, e.icon, qualityOf(e.link), e.name, ((e.why or ""):gsub("^%l", string.upper)))
    end
  end

  if r.auction and #r.auction > 0 then
    S.header(panel, "Auction House", "Interface\\Icons\\INV_Misc_Coin_01", #r.auction)
    S.note(panel, "Worth more there than at a vendor (prices from Auctionator's last scan). Any Auction House: "
      .. "Stormwind, Ironforge or Darnassus. Sales arrive in your mailbox.")
    for _, e in ipairs(r.auction) do
      local n = e.count or 1
      S.item(panel, e.link, e.icon, qualityOf(e.link), e.name,
        ("About %s at the AH; a vendor pays %s"):format(money(e.ah * n), money(e.vendor * n)))
    end
  end

  -- Exactly what the vendor autopilot sells (grey junk shown as one row).
  local toSell = {}
  for _, e in ipairs(autoSellList and autoSellList(r) or r.unusable) do
    if qualityOf(e.link) ~= 0 then table.insert(toSell, e) end
  end
  local sellCount = #toSell + (#r.junk > 0 and 1 or 0)
  local atShop = MerchantFrame and MerchantFrame:IsShown()
  S.header(panel, "Sell at a vendor", "Interface\\Icons\\INV_Misc_Coin_02", sellCount,
    (atShop and sellCount > 0) and "Sell all" or nil, function()
      local n, left = 0, 0
      for _, e in ipairs(toSell) do
        local ok, why = sellEntry(e)
        if ok then n = n + 1 elseif why == "full" then left = left + 1 end
      end
      if n > 0 then say(("sold %d item%s."):format(n, n == 1 and "" or "s")) end
      if #r.junk > 0 then sellJunk(left)
      else
        if left > 0 then sayMoreToSell(left) end
        C_Timer.After(0.5, refresh)
      end
    end)
  if sellCount == 0 then S.note(panel, "Nothing to sell: your bags only hold things you use.")
  elseif not atShop then
    S.note(panel, DruidKitDB and DruidKitDB.autoSell == false and "Talk to any vendor and Sell buttons appear here."
      or "Talk to any vendor: these are sold for you, and your gear is repaired.")
  end
  if #r.junk > 0 then
    local first = r.junk[1]
    S.item(panel, nil, first.icon, 0, ("%d grey item%s"):format(#r.junk, #r.junk == 1 and "" or "s"),
      ("Worth %s."):format(money(r.junkValue)), atShop and "Sell" or nil, atShop and function() sellJunk() end or nil)
  end
  for _, e in ipairs(toSell) do
    S.item(panel, e.link, e.icon, qualityOf(e.link), e.name .. ((e.count or 1) > 1 and ("  x" .. e.count) or ""),
      ((e.why or "sell it"):gsub("^%l", string.upper)),
      atShop and "Sell" or nil, atShop and function() sellOne(e, #toSell + #r.junk) end or nil)
  end

  S.header(panel, "Bags full? Drop these first", "Interface\\Icons\\INV_Misc_Bag_07_Black", math.min(#r.drop, 5))
  if #r.drop == 0 then
    S.note(panel, "Nothing safe to drop: everything in your bags is useful.")
  else
    local atVendor = MerchantFrame and MerchantFrame:IsShown()
    S.note(panel, atVendor and "You're at a vendor: Sell gets money for it. Cheapest first."
      or "Destroy asks you to confirm first. At a vendor these become Sell buttons. Cheapest first.")
    for n, e in ipairs(r.drop) do
      if n > 5 then break end
      local q = qualityOf(e.link)
      S.item(panel, e.link, e.icon, q, e.name .. (e.count > 1 and ("  |cffffffffx" .. e.count .. "|r") or ""),
        ("%s%s"):format((e.why:gsub("^%l", string.upper)), e.value > 0 and (", sells for " .. money(e.value)) or ""),
        atVendor and "Sell" or "Destroy", function()
          if atVendor then
            sellOne(e)
          else
            DruidKit_ConfirmDestroy(e)
          end
        end)
    end
  end

  S.finish(panel)
  panel.footer:SetText("Never suggests quest items, library books, herbs, anything your quests need, recipe materials, potions, your best 2 food and 2 drink stacks, or your best fishing pole.")
end

-- Destroy with a clear yes/no. Nothing is deleted unless you click Destroy in the dialog.
StaticPopupDialogs["DRUIDKIT_DESTROY"] = {
  text = "Destroy %s?\n\nIt's gone for good. %s",
  button1 = "Destroy", button2 = "Keep it",
  OnAccept = function(self, data)
    if not data then return end
    if slotInfo(data.bag, data.slot) ~= data.link then
      say("not destroyed: that bag slot has changed since you clicked. Open Bag check again.")
      return
    end
    local guard = protectedReason(data.link, data.bag, data.slot)
    if guard then say("not destroyed: " .. guard .. ".") return end
    ClearCursor()
    if C_Container and C_Container.PickupContainerItem then C_Container.PickupContainerItem(data.bag, data.slot) else PickupContainerItem(data.bag, data.slot) end
    local ok = pcall(DeleteCursorItem)
    if not ok then
      say("WoW wants you to finish this yourself: the item is on your cursor, click the ground, then confirm.")
      return
    end
    C_Timer.After(0.4, refresh)
  end,
  OnCancel = function() ClearCursor() end,
  timeout = 0, whileDead = true, hideOnEscape = true, showAlert = true,
}
function DruidKit_ConfirmDestroy(e)
  local worth = (e.value or 0) > 0 and ("It would sell for " .. money(e.value) .. " at a vendor.") or "It has no vendor value."
  local dlg = StaticPopup_Show("DRUIDKIT_DESTROY", e.link .. ((e.count or 1) > 1 and (" x" .. e.count) or ""), worth)
  if dlg then dlg.data = { bag = e.bag, slot = e.slot, link = e.link } end
end

local function toggle()
  S = S or DruidKitStyle
  if not panel then
    panel = S.window("DruidKitBagCheck", "Bag check", "Interface\\Icons\\INV_Misc_Bag_08", 400, 470)
    panel:SetPoint("RIGHT", UIParent, "RIGHT", -240, 0)
  end
  if panel:IsShown() then panel:Hide() else panel:Show(); invalidate(); refresh() end
end
DruidKit_ToggleBags = toggle

-- Tooltip line on upgrades --------------------------------------------------------------
local function tooltipLine(tt, link)
  if not link then return end
  if isBook((getInfo(link))) then
    tt:AddLine("Druid Kit: library book. Hand in to Garion Wendell, Stormwind library. Don't sell or destroy it.", 0.5, 0.83, 0.36, true)
    return
  end
  local why = not upgradeFor(link) and keepReason(link)
  if why then tt:AddLine("Druid Kit: keep, " .. why, 0.5, 0.83, 0.36) end
  local gain, slotName = upgradeFor(link)
  if gain then tt:AddLine(("Druid Kit: upgrade for your %s (+%d)"):format(slotName:lower(), math.floor(gain + 0.5)), 0.5, 0.83, 0.36) end
end
if TooltipDataProcessor and Enum and Enum.TooltipDataType and Enum.TooltipDataType.Item then
  TooltipDataProcessor.AddTooltipPostCall(Enum.TooltipDataType.Item, function(tt, data)
    if tt ~= GameTooltip and tt ~= ItemRefTooltip then return end
    local _, link = tt:GetItem()
    pcall(tooltipLine, tt, link)
  end)
elseif GameTooltip:HasScript("OnTooltipSetItem") then
  GameTooltip:HookScript("OnTooltipSetItem", function(tt) local _, link = tt:GetItem(); pcall(tooltipLine, tt, link) end)
end

-- Sell junk button at vendors ---------------------------------------------------------
local sellBtn
sellJunk = function(left)
  left = type(left) == "number" and left or 0
  local sold, total = 0, 0
  for bag = 0, 4 do
    for slot = 1, (numSlots(bag) or 0) do
      local link, count, quality, _, _, locked = slotInfo(bag, slot)
      if link and not locked then
        local _, _, q, _, _, _, _, _, _, _, price = getInfo(link)
        if (q or quality) == 0 and (price or 0) > 0 and not protectedReason(link, bag, slot) then
          if buybackLeft() <= 0 then
            left = left + 1
          else
            useSlot(bag, slot)
            soldThisVisit = soldThisVisit + 1
            logSale((getInfo(link)), count, "grey junk")
            sold = sold + 1; total = total + price * (count or 1)
          end
        end
      end
    end
  end
  if sold > 0 then say(("sold %d grey item%s for %s."):format(sold, sold == 1 and "" or "s", money(total)))
  elseif left == 0 then say("no grey items to sell.") end
  if left > 0 then sayMoreToSell(left) end
  C_Timer.After(0.5, refresh)
end
-- Mount money: Apprentice Riding is 100g at level 40 (the mount comes with it). Target grows with level (quests pay
-- more gold later), so being behind early is normal; the line says how far.
local MOUNT_GOLD = 100 * 10000
local function mountTarget(lvl)
  if lvl >= 40 then return MOUNT_GOLD end
  if lvl <= 20 then return 0 end
  return math.floor(MOUNT_GOLD * ((lvl - 20) / 20) ^ 1.5)
end
local function mountLine()
  local have = (GetMoney and GetMoney()) or 0
  local lvl = UnitLevel("player") or 1
  local target = mountTarget(lvl)
  local head = ("Mount money: %s of 100g"):format(money(have))
  if have >= MOUNT_GOLD then return head .. ": ENOUGH. Train riding at 40." end
  if target == 0 then return head .. ": start saving now (about 3g by level 22)." end
  if have >= target then return head .. (": on track (aim for %s at level %d)."):format(money(target), lvl) end
  return head .. (": BEHIND by %s (aim for %s at level %d). Sell on the Auction House, skip buys you don't need.")
    :format(money(target - have), money(target), lvl)
end
DruidKit_MountLine = function() local ok, l = pcall(mountLine); return ok and l or nil end
DruidKit_MountTarget = mountTarget

-- Autopilot at every vendor (on unless /dk autosell off): sell grey junk, gear druids can't use or that's worse
-- than yours, and spare materials; then repair. Kept: quest items, upgrades, gear sets, bank items, anything
-- worth more on the Auction House, and green or better Bind on Equip gear (sell those on the Auction House).
-- Mistakes: the vendor's Buyback tab has the last 12 items, so no more than that are sold per visit.
local autoBusy = false
local function bindTypeOf(link) return select(14, getInfo(link)) end
-- What the autopilot sells (player, 19 Nov: "fine to sell ingredients I have no recipe for"): grey junk; gear that's
-- worse or not for druids; items for another class or profession; materials no recipe of yours uses (herbs and
-- anything a recipe in your bags needs are kept); and worse bandages. Never potions, elixirs, flasks or scrolls (the
-- Bag check footer promises that), never food or drink (cooked food is the +5% XP buff), never quest items.
local CONSUMABLE = { [1] = true, [2] = true, [3] = true, [4] = true }   -- potion, elixir, flask, scroll
local BANDAGE = 7
-- Classic item data often files potions, elixirs, scrolls and bandages under subclass 0: use the name too.
local function consumableKind(name, subID)
  if CONSUMABLE[subID] or subID == BANDAGE then return subID end
  name = name or ""
  if name:find("Bandage") then return BANDAGE end
  if name:find("Potion") then return 1 end
  if name:find("^Elixir") then return 2 end
  if name:find("Flask") then return 3 end
  if name:find("^Scroll of") then return 4 end
end
DruidKit_ConsumableKind = consumableKind

-- Materials named in the recipes you carry (not learned yet): keep them.
local function recipeMats()
  local names = {}
  for bag = 0, 4 do
    for slot = 1, (numSlots(bag) or 0) do
      local link = slotInfo(bag, slot)
      if link and select(12, getInfo(link)) == 9 then
        for _, t in ipairs(tooltipLines(link) or {}) do names[#names + 1] = t end
      end
    end
  end
  local text = table.concat(names, "\n")
  return function(name) return name and name ~= "" and text:find(name, 1, true) ~= nil end
end

-- Bandages: keep every stack of your best bandage; worse bandages go once you have 10 of the best.
local function bandageExtras()
  local groups = {}
  for bag = 0, 4 do
    for slot = 1, (numSlots(bag) or 0) do
      local link, count = slotInfo(bag, slot)
      if link then
        local name, _, q, ilvl, _, _, _, _, _, _, price, classID, subID = getInfo(link)
        if classID == 0 and consumableKind(name, subID) == BANDAGE and (price or 0) > 0 and (q or 1) >= 1
          and not questInfo(bag, slot) then
          local g = groups[name] or { name = name, ilvl = ilvl or 0, total = 0, stacks = {} }
          g.total = g.total + (count or 1)
          table.insert(g.stacks, { bag = bag, slot = slot, link = link, count = count or 1, name = name })
          groups[name] = g
        end
      end
    end
  end
  local best
  for _, g in pairs(groups) do if not best or g.ilvl > best.ilvl then best = g end end
  local out = {}
  if not best or best.total < 10 then return out end
  for _, g in pairs(groups) do
    if g ~= best then
      for _, st in ipairs(g.stacks) do
        st.why = "worse bandage: you have " .. best.total .. " " .. best.name
        table.insert(out, st)
      end
    end
  end
  return out
end

autoSellList = function(r)
  local out = {}
  local needed = recipeMats()
  local function addAll(list, kind)
    for _, e in ipairs(list or {}) do
      local link = e.link
      local name, _, q, _, _, _, _, _, equipLoc, _, value, classID, subID = getInfo(link)
      local boeGood = (q or 0) >= 2 and bindTypeOf(link) == 2
      local ok = true
      if kind == "gear" then
        ok = (equipLoc and equipLoc ~= "" and classID ~= 0) or restriction(link) ~= nil
        local w = cantWield(link)
        if w and w:find("haven't learned", 1, true) and (q or 0) >= 2 then ok = false end   -- train the skill, then it may be an upgrade
        if classID == 0 and not restriction(link) then ok = false end   -- food/drink/consumables: never from here
        if classID == 7 or classID == 5 then ok = false end
      elseif kind == "mats" then
        ok = (classID == 7 or classID == 5) and not (classID == 7 and subID == 9) and not needed(name)
      end
      if ok and (value or 0) > 0 and not boeGood and not protectedReason(link, e.bag, e.slot) then table.insert(out, e) end
    end
  end
  addAll(r.junk, "junk"); addAll(r.unusable, "gear"); addAll(r.spare, "mats"); addAll(bandageExtras(), "extra")
  return out
end

-- How many things the next vendor visit would sell (the step window's sell steps use it).
DruidKit_SellCount = function()
  local ok, n = pcall(function() return #autoSellList(scan()) end)
  return ok and n or nil
end

-- Buff button (step window): the next elixir, flask or scroll in your bags whose buff you don't have.
local function hasAura(spell)
  if not spell then return false end
  if C_UnitAuras and C_UnitAuras.GetAuraDataBySpellName then
    return C_UnitAuras.GetAuraDataBySpellName("player", spell, "HELPFUL") ~= nil
  end
  if AuraUtil and AuraUtil.FindAuraByName then return AuraUtil.FindAuraByName(spell, "player") ~= nil end
  return false
end
local function nextBuff()
  local lvl = UnitLevel("player") or 1
  local seen, list = {}, {}
  for bag = 0, 4 do
    for slot = 1, (numSlots(bag) or 0) do
      local link, count = slotInfo(bag, slot)
      if link then
        local name, _, _, _, minLevel, _, _, _, _, icon, _, classID, subID = getInfo(link)
        local kind = classID == 0 and consumableKind(name, subID)
        if (kind == 2 or kind == 3 or kind == 4) and (minLevel or 0) <= lvl and not seen[name]
          and not questInfo(bag, slot) and not restriction(link) then
          seen[name] = true
          local spell = GetItemSpell and GetItemSpell(link)
          if spell and not hasAura(spell) then
            table.insert(list, { name = name, icon = icon, count = count or 1, spell = spell })
          end
        end
      end
    end
  end
  table.sort(list, function(a, b) return a.name < b.name end)
  return list[1], list
end
DruidKit_NextBuff = function() local ok, a, b = pcall(nextBuff); if ok then return a, b end end

local function autoPilot()
  if autoBusy or not (DruidKitDB and DruidKitDB.autoSell ~= false) then return end
  local r = scan()
  local list = autoSellList(r)
  autoBusy = true
  local sold, total, i = 0, 0, 0
  local function finish()
    autoBusy = false
    local repaired = 0
    if CanMerchantRepair and CanMerchantRepair() and GetRepairAllCost then
      local cost, need = GetRepairAllCost()
      if need and cost and cost > 0 and (GetMoney() or 0) >= cost then RepairAllItems(); repaired = cost end
    end
    local parts = {}
    if sold > 0 then table.insert(parts, ("sold %d item%s for %s"):format(sold, sold == 1 and "" or "s", money(total))) end
    if repaired > 0 then table.insert(parts, "repaired for " .. money(repaired)) end
    if #parts > 0 then
      say(table.concat(parts, ", ") .. ". Sold something by mistake? The vendor's Buyback tab has it.")
      say(mountLine())
    end
    if #list >= i then sayMoreToSell(#list - i + 1) end
    if r.auction and #r.auction > 0 then
      say(("%d item%s worth more on the Auction House: kept (Alt+B lists them)."):format(#r.auction, #r.auction == 1 and "" or "s"))
    end
    C_Timer.After(0.5, function() pcall(refresh) end)
  end
  local function step()
    i = i + 1
    local e = list[i]
    if not e or buybackLeft() <= 0 or not (MerchantFrame and MerchantFrame:IsShown()) then return finish() end
    if slotInfo(e.bag, e.slot) == e.link then
      useSlot(e.bag, e.slot)
      soldThisVisit = soldThisVisit + 1
      -- Sold log (last 60): the update reads it, so nothing the autopilot sells is a mystery.
      logSale(e.name or (getInfo(e.link)), e.count, e.why)
      sold = sold + 1
      total = total + (select(11, getInfo(e.link)) or 0) * (e.count or 1)
    end
    C_Timer.After(0.2, step)
  end
  step()
end
DruidKit_AutoPilot = autoPilot

local function showSellButton()
  if not MerchantFrame then return end
  if not sellBtn then
    sellBtn = CreateFrame("Button", "DruidKitSellJunk", MerchantFrame, "UIPanelButtonTemplate")
    sellBtn:SetSize(96, 22)
    sellBtn:SetPoint("TOPRIGHT", MerchantFrame, "TOPRIGHT", -40, -40)
    sellBtn:SetText("Sell junk")
    sellBtn:SetScript("OnClick", sellJunk)
  end
  local r = scan()
  sellBtn:SetEnabled(#r.junk > 0)
  sellBtn:Show()
end

-- Events ------------------------------------------------------------------------------
local known = {}
local loggedIn = false
-- Quest starters you haven't used: told once per session when they reach your bags, and listed for the step
-- window ("Quest to start in your bags").
local startersSaid = {}
local function startersWaiting(r)
  local out = {}
  for _, e in ipairs(r.use or {}) do
    if e.why and e.why:find("^starts a quest") then table.insert(out, e) end
  end
  return out
end
DruidKit_QuestStarters = function()
  local ok, r = pcall(function() return startersWaiting(results) end)
  return ok and r or {}
end

local function announceNewUpgrades()
  local r = scan()
  for _, e in ipairs(startersWaiting(r)) do
    if not startersSaid[e.name] and loggedIn then
      startersSaid[e.name] = true
      local msg = ("Starts a quest: %s. Open your bags and right-click it."):format(e.name)
      if RaidNotice_AddMessage and RaidWarningFrame then
        pcall(RaidNotice_AddMessage, RaidWarningFrame, msg, { r = 1, g = 0.82, b = 0 })
      end
      say(msg)
    end
  end
  for _, e in ipairs(r.upgrades) do
    if not known[e.link] and loggedIn then
      known[e.link] = true
      local msg = ("Upgrade in your bags: %s (%s)"):format(e.name, e.slotName)
      if RaidNotice_AddMessage and RaidWarningFrame and ChatTypeInfo then
        pcall(RaidNotice_AddMessage, RaidWarningFrame, msg, { r = 0.5, g = 0.83, b = 0.36 })
      end
      say(msg .. ". /dk bags to equip.")
    end
    known[e.link] = true
  end
  refresh()
end

local ev = CreateFrame("Frame")
for _, e in ipairs({ "PLAYER_LOGIN", "BAG_UPDATE_DELAYED", "PLAYER_EQUIPMENT_CHANGED", "MERCHANT_SHOW", "MERCHANT_CLOSED", "PLAYER_LEVEL_UP" }) do
  pcall(ev.RegisterEvent, ev, e)
end
local pending = false
ev:SetScript("OnEvent", function(_, e)
  if e ~= "MERCHANT_CLOSED" then invalidate() end
  if e == "PLAYER_LOGIN" then
    C_Timer.After(5, function()
      pcall(scan)
      for _, x in ipairs(results.upgrades) do known[x.link] = true end
      loggedIn = true
      local n = #results.upgrades
      if n > 0 then say(("%d gear upgrade%s in your bags. /dk bags to see and equip."):format(n, n == 1 and "" or "s")) end
    end)
    return
  end
  if e == "MERCHANT_SHOW" then
    soldThisVisit = 0
    pcall(showSellButton)
    C_Timer.After(0.3, function() pcall(autoPilot) end)
    C_Timer.After(0.2, function() pcall(refresh) end)
    return
  end
  if e == "PLAYER_LEVEL_UP" then C_Timer.After(2, function() local l = DruidKit_MountLine(); if l then say(l) end end) end
  if e == "MERCHANT_CLOSED" then C_Timer.After(0.2, function() pcall(refresh) end) return end
  if pending then return end
  pending = true
  C_Timer.After(1, function() pending = false; pcall(announceNewUpgrades) end)
end)

-- Shared with the bank helper
DruidKitBagsAPI = {
  getInfo = getInfo, slotInfo = slotInfo, questInfo = questInfo, numSlots = numSlots, useSlot = useSlot,
  upgradeFor = upgradeFor, isTool = isTool, refresh = function() invalidate(); refresh() end,
}

-- Loot helper and roll advisor --------------------------------------------------------
-- Bags full while looting: says, for each item, TAKE (and what to drop first) or SKIP.
-- Group rolls: says NEED, GREED or PASS with the reason, and has the three buttons.
-- Advice is words, not colours. Nothing is dropped or rolled without your click.
local FONT = "Fonts\\FRIZQT__.TTF"
local GOLDC = { 0.85, 0.68, 0.3 }
local function txt(parent, size)
  local fs = parent:CreateFontString(nil, "OVERLAY"); fs:SetFont(FONT, size, "OUTLINE"); fs:SetJustifyH("LEFT"); fs:SetWordWrap(true)
  return fs
end
local function box(name, w)
  local f = CreateFrame("Frame", name, UIParent, "BackdropTemplate")
  f:SetWidth(w); f:SetFrameStrata("DIALOG"); f:SetClampedToScreen(true)
  f:SetMovable(true); f:EnableMouse(true); f:RegisterForDrag("LeftButton")
  f:SetScript("OnDragStart", f.StartMoving); f:SetScript("OnDragStop", f.StopMovingOrSizing)
  if f.SetBackdrop then
    f:SetBackdrop({ bgFile = "Interface\\Buttons\\WHITE8x8", edgeFile = "Interface\\Tooltips\\UI-Tooltip-Border", edgeSize = 14,
                    insets = { left = 3, right = 3, top = 3, bottom = 3 } })
    f:SetBackdropColor(0.02, 0.07, 0.03, 0.95); f:SetBackdropBorderColor(GOLDC[1], GOLDC[2], GOLDC[3], 1)
  end
  f.title = txt(f, 14); f.title:SetPoint("TOPLEFT", 10, -8); f.title:SetTextColor(GOLDC[1], GOLDC[2], GOLDC[3])
  f.rows = {}
  f:Hide()
  return f
end
local function button(parent, label, w)
  local b = CreateFrame("Button", nil, parent, "UIPanelButtonTemplate")
  b:SetSize(w or 70, 24); b:SetText(label)
  return b
end
local function stacksWithBags(link)
  local id = itemID(link); if not id then return false end
  local stackMax = select(8, getInfo(link)) or 1
  if stackMax <= 1 then return false end
  for bag = 0, 4 do
    for slot = 1, (numSlots(bag) or 0) do
      local l, count = slotInfo(bag, slot)
      if l and itemID(l) == id and (count or 1) < stackMax then return true end
    end
  end
  return false
end

-- Verdict for one item: "take"/"skip", reason, and the bag item to drop first (or nil)
local function lootVerdict(link, qty, isQuest, cheapest)
  if isQuest then return "take", "quest item" end
  local guard = protectedReason(link)
  if guard then return "take", guard end
  local name, _, q, _, _, _, _, _, _, _, price = getInfo(link)
  if name and name:find("Waylaid") then return "take", "Waylaid Crate: fill it for Merchant's Favor" end
  if stacksWithBags(link) then return "take", "stacks with what you have: no new slot" end
  local gain, slotName = upgradeFor(link)
  if gain then return "take", ("upgrade for your %s (+%d)"):format(slotName:lower(), math.floor(gain + 0.5)) end
  local keep = keepReason(link)
  if keep then return "take", keep end
  if name and DruidKit_NeededFor then
    local need, _, used = DruidKit_NeededFor(name)
    if need or used then return "take", "your recipes use it" end
  end
  local value = (price or 0) * (qty or 1)
  if not cheapest then return "skip", "everything in your bags is worth keeping" end
  if value > (cheapest.value or 0) then
    return "take", ("sells for %s, more than %s (%s)"):format(money(value), cheapest.name, money(cheapest.value or 0))
  end
  return "skip", ("sells for %s: worth less than anything you'd drop"):format(money(value))
end

local lootBox
-- Gear worth stopping for while the bags are full: an upgrade, a piece for your other set, or a green or better
-- item worth more than what you'd drop. Shouted on screen (with a sound as second signal), and again if you
-- walk away and leave it on the corpse.
local lootPending = {}      -- loot slot -> { name, link, why } for items worth taking that are still in the loot
local lootShouted = {}      -- link -> time of the last shout
local function clearPending() for k in pairs(lootPending) do lootPending[k] = nil end end
-- Worth stopping for: upgrades and set pieces; any green or better gear; and anything (white weapons too) that sells
-- for 20 silver or more at a vendor, or 50 silver on the Auction House.
local function important(link, why, verdict, qty)
  if verdict ~= "take" or not link then return false end
  local _, _, q, _, _, _, _, _, equipLoc, _, price = getInfo(link)
  if upgradeFor(link) or keepReason(link) then return true end
  if equipLoc ~= nil and equipLoc ~= "" and (q or 0) >= 2 then return true end
  if (price or 0) * (qty or 1) >= 2000 then return true end
  local ah = ahPrice(link)
  return ah ~= nil and ah * (qty or 1) >= 5000
end
local function bigAlert(msg)
  if RaidNotice_AddMessage and RaidWarningFrame then
    pcall(RaidNotice_AddMessage, RaidWarningFrame, msg, { r = 1, g = 0.82, b = 0 })
  end
  if PlaySound and SOUNDKIT and SOUNDKIT.RAID_WARNING then pcall(PlaySound, SOUNDKIT.RAID_WARNING) end
  say(msg)
end
local function lootLeftBehind()
  local left = {}
  for _, it in pairs(lootPending) do table.insert(left, it) end
  clearPending()
  if #left == 0 then return end
  local it = left[1]
  bigAlert(("LEFT ON THE CORPSE: %s (%s). Make room (Alt+B shows what to drop), then loot the corpse again.")
    :format(it.name, it.why) .. (#left > 1 and (" +" .. (#left - 1) .. " more.") or ""))
end
DruidKit_LootLeftBehind = lootLeftBehind

local function showLootHelp()
  local free = freeSlots()
  if free > 0 then if lootBox then lootBox:Hide() end return end   -- room now: you can click it
  clearPending()
  lootBox = lootBox or box("DruidKitLootHelp", 330)
  lootBox.title:SetText("Bags full: what to take")
  for _, r in ipairs(lootBox.rows) do r:Hide() end
  local res = scan()
  local cheapest = res.drop and res.drop[1]
  local y, n = -30, 0
  for i = 1, (GetNumLootItems and GetNumLootItems() or 0) do
    local slotType = GetLootSlotType and GetLootSlotType(i)
    local icon, name, qty, _, quality, _, isQuest = GetLootSlotInfo(i)
    if name then
      n = n + 1
      local row = lootBox.rows[n]
      if not row then
        row = CreateFrame("Frame", nil, lootBox); row:SetSize(310, 40)
        row.icon = row:CreateTexture(nil, "ARTWORK"); row.icon:SetSize(30, 30); row.icon:SetPoint("LEFT", 0, 0)
        row.verdict = txt(row, 13); row.verdict:SetPoint("TOPLEFT", row.icon, "TOPRIGHT", 8, 0); row.verdict:SetWidth(270)
        row.why = txt(row, 13); row.why:SetPoint("TOPLEFT", row.verdict, "BOTTOMLEFT", 0, -2); row.why:SetWidth(270)
        lootBox.rows[n] = row
      end
      row:SetPoint("TOPLEFT", 10, y); row.icon:SetTexture(icon)
      local verdict, why
      if slotType and slotType ~= 1 then verdict, why = "take", "money or currency: needs no bag space"
      else
        local link = GetLootSlotLink and GetLootSlotLink(i)
        if link then verdict, why = lootVerdict(link, qty, isQuest, cheapest) else verdict, why = "take", "" end
        if important(link, why, verdict, qty) then
          lootPending[i] = { name = name, link = link, why = why }
          local now = (GetTime and GetTime()) or 0
          if not lootShouted[link] or now - lootShouted[link] > 60 then
            lootShouted[link] = now
            bigAlert(("BAGS FULL, but this loot is worth taking: %s (%s).%s"):format(name, why or "",
              cheapest and (" Destroy " .. cheapest.name .. " to make room.") or ""))
          end
        end
      end
      row.verdict:SetText((verdict == "take" and "|cff7fd35bTAKE|r  " or "|cffff6060SKIP|r  ") .. name)
      row.why:SetText(why or ""); row:Show()
      y = y - 44
    end
  end
  if not lootBox.drop then
    lootBox.drop = button(lootBox, "Make room", 300)
    lootBox.dropText = txt(lootBox, 13)
  end
  if cheapest then
    lootBox.dropText:ClearAllPoints(); lootBox.dropText:SetPoint("TOPLEFT", 10, y - 2); lootBox.dropText:SetWidth(310)
    lootBox.dropText:SetText(("To take one: destroy |cffffd100%s|r (%s, %s), then click the item."):format(cheapest.name, cheapest.why or "", money(cheapest.value or 0)))
    lootBox.dropText:Show()
    lootBox.drop:ClearAllPoints(); lootBox.drop:SetPoint("TOPLEFT", 10, y - 34)
    lootBox.drop:SetText("Destroy " .. cheapest.name)
    lootBox.drop:SetScript("OnClick", function() DruidKit_ConfirmDestroy(cheapest) end)
    lootBox.drop:Show()
    y = y - 64
  else
    lootBox.dropText:Hide(); lootBox.drop:Hide()
  end
  lootBox:SetHeight(-y + 10)
  lootBox:ClearAllPoints()
  if LootFrame and LootFrame:IsShown() then lootBox:SetPoint("TOPLEFT", LootFrame, "TOPRIGHT", 8, 0)
  else lootBox:SetPoint("CENTER", UIParent, "CENTER", 260, 80) end
  lootBox:Show()
end

-- Rolls
local rollBox
local rolls = {}      -- rollID -> info
local autoRolled = {} -- rollID -> roll we made by ourselves
-- Who else in the party wears what (for polite rolling). Hunters and shamans wear leather until 40.
local CLOTH = { MAGE = "mage", PRIEST = "priest", WARLOCK = "warlock" }
local LEATHER = { ROGUE = "rogue", DRUID = "druid", HUNTER = "hunter", SHAMAN = "shaman" }
local function partyWearers(subID)
  local list = {}
  for i = 1, 4 do
    local u = "party" .. i
    if UnitExists and UnitExists(u) then
      local _, cls = UnitClass(u)
      local lvl = UnitLevel(u) or 0
      if subID == 1 and CLOTH[cls] then table.insert(list, CLOTH[cls])
      elseif subID == 2 and LEATHER[cls] and not ((cls == "HUNTER" or cls == "SHAMAN") and lvl >= 40) then
        table.insert(list, LEATHER[cls]) end
    end
  end
  return list
end
local SMALL = 3   -- upgrades below this are "small"
local function rollAdvice(link, canNeed, canGreed)
  local _, _, quality, _, _, _, _, _, equipLoc, _, price, classID, subID, bindType = getInfo(link)
  local sells = money(price or 0)
  local isArmour = classID == 4 and (subID == 1 or subID == 2)
  local others = isArmour and partyWearers(subID) or {}
  local who = others[1]
  if classID == 9 and canGreed then
    return "GREED", "recipe: Greed. If you want it for your profession, ask in /p first", 2
  end
  if (classID == 7 or classID == 5) and canGreed then
    return "GREED", ("crafting material: Greed (sells for %s)"):format(sells), 2, true
  end
  local gain, slotName = upgradeFor(link)
  if gain and canNeed then
    local g = math.floor(gain + 0.5)
    if subID == 1 and classID == 4 and who then
      if gain < SMALL then
        return "GREED", ("small upgrade (+%d) but cloth is the %s's armour: be nice, Greed"):format(g, who), 2
      end
      return "NEED", ("big upgrade (+%d %s). Cloth: ask in /p first, \"ok if I Need?\""):format(g, slotName:lower()), 1
    end
    if who and gain < SMALL then
      return "GREED", ("only a small upgrade (+%d). The %s may want it more: Greed is the kind choice"):format(g, who), 2
    end
    if who then
      return "NEED", ("upgrade for your %s (+%d). The %s may roll too: that's fair"):format(slotName:lower(), g, who), 1
    end
    return "NEED", ("upgrade for your %s (+%d)"):format(slotName:lower(), g), 1
  end
  -- Too high level for you today, but you'll grow into it (within 5 levels)
  local minLevel = select(5, getInfo(link)) or 0
  local myLevel = UnitLevel("player") or 0
  if minLevel > myLevel and minLevel - myLevel <= 5 then
    local later, laterSlot = upgradeFor(link, nil, true)
    if later and canNeed and bindType == 1 and minLevel - myLevel <= 4 and later >= SMALL and not keepReason(link) then
      return "NEED", ("upgrade for your %s at level %d (+%d), binds when picked up: Need is fair for your role. "
        .. "Say in /p \"need for level %d\""):format(laterSlot:lower(), minLevel, math.floor(later + 0.5), minLevel), 1
    end
    if later and canGreed then
      return "GREED", ("upgrade for your %s at level %d (+%d): Greed. If nobody Needs it, ask in /p if you can have it"):format(
        laterSlot:lower(), minLevel, math.floor(later + 0.5)), 2
    end
  end
  local other = keepReason(link)
  if other and canGreed then
    return "GREED", ("off-role piece (%s): Greed, so main-role players get first pick"):format(other), 2
  end
  if other and canNeed then return "NEED", other, 1 end
  if canGreed then
    if equipLoc and equipLoc ~= "" and not usable(classID, subID, equipLoc) then
      local kind = (classID == 4 and (subID == 3 and "mail" or subID == 4 and "plate" or subID == 6 and "a shield"))
        or (classID == 2 and "that weapon type") or "it"
      return "GREED", ("druids can never use %s; sells for %s"):format(kind, sells), 2, true
    end
    local tail = ""
    if bindType == 2 and (quality or 0) >= 2 then tail = ". Never Need just to sell it" end
    if who and equipLoc and equipLoc ~= "" then tail = (". The %s may Need it"):format(who) .. tail end
    return "GREED", ("not an upgrade for you; sells for %s%s"):format(sells, tail), 2, not who
  end
  return "PASS", "you can't roll Greed on this", 0
end
DruidKitBagsAPI.rollAdvice = rollAdvice

-- Best gear in your bags for a role ("heal" or "quest"): the biggest upgrade per equip slot type, by that role's
-- weights. Only gear you can wear now (level, armour type, weapon skill, no red tooltip line).
-- Returns { { link = , gain = , slot = "chest" }, ... } (21 Nov: healing mode never swapped gear, no set saved).
DruidKitBagsAPI.bestSet = function(mode)
  local w = mode == "heal" and HEAL_WEIGHTS or WEIGHTS
  local best = {}
  for bag = 0, 4 do
    for slot = 1, (safe(numSlots, bag) or 0) do
      local link = select(1, safe(slotInfo, bag, slot))
      if link then
        local ok, gain, slotName = pcall(upgradeFor, link, w)
        local loc = ok and gain and select(9, getInfo(link))
        if loc then
          if loc == "INVTYPE_ROBE" then loc = "INVTYPE_CHEST" end
          if not best[loc] or gain > best[loc].gain then best[loc] = { link = link, gain = gain, slot = slotName } end
        end
      end
    end
  end
  local out = {}
  for _, e in pairs(best) do table.insert(out, e) end
  table.sort(out, function(a, b) return a.gain > b.gain end)
  return out
end
DruidKitBagsAPI.protectedReason = protectedReason

local function drawRolls()
  rollBox = rollBox or box("DruidKitRolls", 360)
  rollBox.title:SetText("Loot roll advice")
  for _, r in ipairs(rollBox.rows) do r:Hide() end
  local y, n = -30, 0
  for id, info in pairs(rolls) do
    n = n + 1
    local row = rollBox.rows[n]
    if not row then
      row = CreateFrame("Frame", nil, rollBox); row:SetSize(340, 70)
      row.icon = row:CreateTexture(nil, "ARTWORK"); row.icon:SetSize(32, 32); row.icon:SetPoint("TOPLEFT", 0, 0)
      row.name = txt(row, 13); row.name:SetPoint("TOPLEFT", row.icon, "TOPRIGHT", 8, 0); row.name:SetWidth(300)
      row.why = txt(row, 13); row.why:SetPoint("TOPLEFT", row.name, "BOTTOMLEFT", 0, -2); row.why:SetWidth(300)
      row.need = button(row, "Need", 74); row.need:SetPoint("BOTTOMLEFT", 40, 0)
      row.greed = button(row, "Greed", 74); row.greed:SetPoint("LEFT", row.need, "RIGHT", 6, 0)
      row.pass = button(row, "Pass", 74); row.pass:SetPoint("LEFT", row.greed, "RIGHT", 6, 0)
      rollBox.rows[n] = row
    end
    row:SetPoint("TOPLEFT", 10, y); row.icon:SetTexture(info.icon)
    row.name:SetText(("|cffffd100%s|r  %s"):format(info.advice, info.name or "?"))
    row.why:SetText(info.why)
    for _, pair in ipairs({ { row.need, 1, "Need" }, { row.greed, 2, "Greed" }, { row.pass, 0, "Pass" } }) do
      local b, choice, label = pair[1], pair[2], pair[3]
      b:SetText(choice == info.pick and (">" .. label .. "<") or label)   -- the advised button is marked
      b:SetEnabled((choice ~= 1 or info.canNeed) and (choice ~= 2 or info.canGreed))
      b:SetScript("OnClick", function()
        pcall(RollOnLoot, id, choice); rolls[id] = nil; drawRolls()
      end)
    end
    row:Show()
    y = y - 76
  end
  if n == 0 then rollBox:Hide() return end
  rollBox:SetHeight(-y + 8)
  if not rollBox.placed then rollBox:SetPoint("TOP", UIParent, "TOP", 0, -140); rollBox.placed = true end
  rollBox:Show()
end
local function onStartRoll(id)
  local link = GetLootRollItemLink and GetLootRollItemLink(id)
  local icon, name, _, _, _, canNeed, canGreed = GetLootRollItemInfo(id)
  if not link then return end
  local advice, why, pick, auto = rollAdvice(link, canNeed, canGreed)
  if auto and pick == 2 and DruidKitDB.autoRoll ~= false then
    autoRolled = autoRolled or {}
    autoRolled[id] = pick
    pcall(RollOnLoot, id, pick)
    say(("Greed on %s (%s). /dk autoroll off to choose yourself."):format(link, why))
    return
  end
  rolls[id] = { icon = icon, name = name, advice = advice, why = why, pick = pick, canNeed = canNeed, canGreed = canGreed }
  drawRolls()
end

local lev = CreateFrame("Frame")
for _, e in ipairs({ "LOOT_OPENED", "LOOT_SLOT_CLEARED", "LOOT_CLOSED", "START_LOOT_ROLL", "CANCEL_LOOT_ROLL", "CONFIRM_LOOT_ROLL" }) do pcall(lev.RegisterEvent, lev, e) end
lev:SetScript("OnEvent", function(_, e, a1)
  if e == "LOOT_SLOT_CLEARED" and a1 then lootPending[a1] = nil end
  if e == "LOOT_OPENED" or e == "LOOT_SLOT_CLEARED" then
    C_Timer.After(0.05, function() local ok, err = pcall(showLootHelp); if not ok then say("loot helper: " .. tostring(err)) end end)
  elseif e == "LOOT_CLOSED" then
    if lootBox then lootBox:Hide() end
    pcall(lootLeftBehind)
  elseif e == "START_LOOT_ROLL" then
    local ok, err = pcall(onStartRoll, a1); if not ok then say("roll advice: " .. tostring(err)) end
  elseif e == "CONFIRM_LOOT_ROLL" then
    -- a Greed we rolled by ourselves on a bind-on-pickup item asks to confirm: confirm it
    if autoRolled and autoRolled[a1] and ConfirmLootRoll then pcall(ConfirmLootRoll, a1, autoRolled[a1]) end
  elseif e == "CANCEL_LOOT_ROLL" then
    if autoRolled then autoRolled[a1] = nil end
    rolls[a1] = nil; pcall(drawRolls)
  end
end)

-- /dk autosell [on|off] and /dk mount (chained in front of the helper commands).
do
  local prev = DruidKit_HelperCommand
  DruidKit_HelperCommand = function(cmd, rest)
    if cmd == "autoroll" then
      rest = (rest or ""):lower()
      DruidKitDB.autoRoll = not (rest == "off")
      say("Automatic Greed on items you can't use, materials and non-upgrades: " .. (DruidKitDB.autoRoll and "on" or "off"))
      return true
    end
    if cmd == "autosell" then
      rest = (rest or ""):lower()
      if rest == "off" then DruidKitDB.autoSell = false elseif rest == "on" or rest == "" then DruidKitDB.autoSell = true end
      say("selling junk and repairing at vendors by itself: " .. (DruidKitDB.autoSell == false and "OFF." or "ON (/dk autosell off stops it)."))
      return true
    elseif cmd == "mount" or cmd == "gold" then
      say(DruidKit_MountLine() or "no money data yet.")
      return true
    end
    return prev and prev(cmd, rest)
  end
end
