-- Druid Kit: bank helper. Opens beside the bank and suggests what to put in and take out.
-- It learns which herbs, vials and cloth you need when you open your Alchemy, First Aid and
-- Cooking windows (recipes that still give skill-ups: orange, yellow or green).

local GREEN, ORANGE, GREY, YELLOW = "|cff7fd35b", "|cffff7c0a", "|cff9d9d9d", "|cffffd100"
local API

-- Learn reagents from profession windows ------------------------------------------------
local USEFUL = { optimal = true, medium = true, easy = true }

local function rememberReagents()
  DruidKitDB.reagents = DruidKitDB.reagents or {}
  DruidKitDB.reagentsAll = DruidKitDB.reagentsAll or {}
  local prof, need, all = nil, {}, {}
  if GetNumTradeSkills and GetTradeSkillInfo and GetTradeSkillLine then
    prof = GetTradeSkillLine()
    for i = 1, (GetNumTradeSkills() or 0) do
      local recipe, kind = GetTradeSkillInfo(i)
      if recipe and kind ~= "header" then
        for j = 1, (GetTradeSkillNumReagents(i) or 0) do
          local name = GetTradeSkillReagentInfo(i, j)
          if name then
            all[name] = recipe
            if USEFUL[kind] then need[name] = recipe end
          end
        end
      end
    end
  elseif C_TradeSkillUI and C_TradeSkillUI.GetAllRecipeIDs then
    local info = C_TradeSkillUI.GetBaseProfessionInfo and C_TradeSkillUI.GetBaseProfessionInfo()
    prof = info and info.professionName
    for _, id in ipairs(C_TradeSkillUI.GetAllRecipeIDs() or {}) do
      local r = C_TradeSkillUI.GetRecipeInfo(id)
      if r and r.learned then
        local sch = C_TradeSkillUI.GetRecipeSchematic(id, false)
        for _, slot in ipairs(sch and sch.reagentSlotSchematics or {}) do
          local item = slot.reagents and slot.reagents[1] and slot.reagents[1].itemID
          local name = item and API.getInfo(item)
          if name then
            all[name] = r.name
            if r.relativeDifficulty and r.relativeDifficulty <= 2 then need[name] = r.name end
          end
        end
      end
    end
  end
  return prof, need, all
end
local GATHER = { Herbalism = true, Fishing = true, Mining = true, Skinning = true }
local function learnReagents()
  -- Read twice: just after switching windows the recipe list can still be the last profession's.
  local p1 = rememberReagents()
  if not p1 or p1 == "UNKNOWN" or GATHER[p1] then return end
  C_Timer.After(0.6, function()
    local ok, prof, need, all = pcall(rememberReagents)
    if ok and prof == p1 and next(all) then DruidKitDB.reagents[prof] = need; DruidKitDB.reagentsAll[prof] = all end
  end)
end

local function neededFor(name)
  for _, list in pairs(DruidKitDB.reagents or {}) do
    if list[name] then return list[name] end
  end
end
local function usedFor(name)
  for _, list in pairs(DruidKitDB.reagentsAll or {}) do
    if list[name] then return list[name] end
  end
end
local function haveReagentData() return next(DruidKitDB.reagentsAll or {}) ~= nil end
local function haveAlchemy() return (DruidKitDB.reagentsAll or {})["Alchemy"] ~= nil end
-- need = gives skill-ups now; used = any recipe you know uses it.
DruidKit_NeededFor = function(name) return neededFor(name), haveReagentData(), usedFor(name) end

-- Bank bag IDs -----------------------------------------------------------------------------
local function bankBags()
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
local PLAYER_BAGS = { 0, 1, 2, 3, 4 }

-- Decide ---------------------------------------------------------------------------------------
local function classify()
  local deposit, take = {}, {}
  local freeBags = 0
  for _, bag in ipairs(PLAYER_BAGS) do
    for slot = 1, (API.numSlots(bag) or 0) do
      local link, count = API.slotInfo(bag, slot)
      if not link then
        freeBags = freeBags + 1
      else
        local name, _, q, _, _, _, _, _, _, icon, _, classID = API.getInfo(link)
        local isQuest = API.questInfo(bag, slot)
        if name and DruidKit_IsLibraryBook and DruidKit_IsLibraryBook(name) then
          table.insert(deposit, { bag = bag, slot = slot, link = link, icon = icon, count = count or 1,
            why = "library book: safe here until you visit the Stormwind library" })
          name = nil
        end
        if name and DruidKit_Protected and DruidKit_Protected(link, bag, slot) then name = nil end  -- quest needs it: keep in bags
        if name and classID == 9 and DruidKit_RecipeCheck then
          local verdict, skill, need, have = DruidKit_RecipeCheck(link)
          if verdict == "later" then
            table.insert(deposit, { bag = bag, slot = slot, link = link, icon = icon, count = count or 1,
              why = ("recipe for %s %d (you're %d)"):format(skill, need, have) })
            name = nil
          end
        end
        local minLevel = select(5, API.getInfo(link)) or 0
        if name and minLevel > (UnitLevel("player") or 0) and API.upgradeFor then
          local later, laterSlot = API.upgradeFor(link, nil, true)
          if later then
            table.insert(deposit, { bag = bag, slot = slot, link = link, icon = icon, count = count or 1,
              why = ("for your %s at level %d"):format(laterSlot:lower(), minLevel) })
            name = nil
          end
        end
        -- Gear for your other role: store it while you're not using it.
        local keepWhy, role = DruidKit_GearKeep and DruidKit_GearKeep(link)
        local mode = DruidKitDB.barMode == "heal" and "heal" or "quest"
        if name and keepWhy and role ~= mode then
          table.insert(deposit, { bag = bag, slot = slot, link = link, icon = icon, count = count or 1,
            why = (role == "heal" and "healing gear: store while you quest" or "bear gear: store while you heal") })
          name = nil
        end
        local subID = select(13, API.getInfo(link))
        local isHerb = classID == 7 and subID == 9
        if name and not isQuest and (classID == 7 or classID == 5) and q ~= 0 and haveReagentData()
           and not usedFor(name) and (not isHerb or haveAlchemy()) then
          table.insert(deposit, { bag = bag, slot = slot, link = link, icon = icon, count = count or 1,
            why = isHerb and "for recipes you haven't learned yet" or "none of your recipes use this" })
        end
      end
    end
  end
  for _, bag in ipairs(bankBags()) do
    for slot = 1, (API.numSlots(bag) or 0) do
      local link, count = API.slotInfo(bag, slot)
      if link then
        local name, _, q, _, _, _, _, _, _, icon, _, classID = API.getInfo(link)
        local isQuest, questID, active = API.questInfo(bag, slot)
        local why
        local recipe = name and neededFor(name)
        local keepWhy, role = DruidKit_GearKeep and DruidKit_GearKeep(link)
        local mode = DruidKitDB.barMode == "heal" and "heal" or "quest"
        if name and DruidKit_QuestItems and DruidKit_QuestItems()[name] then why = "your quest needs this"
        elseif keepWhy and role == mode then why = (mode == "heal" and "healing set: you're in healing mode" or "questing set: you're questing")
        elseif recipe then why = "for " .. recipe
        elseif isQuest and (active or not questID) then why = "quest item"
        elseif classID == 0 then why = "potion, food or bandage: handy while questing"
        else
          local gain, slotName = API.upgradeFor(link)
          if gain then why = ("upgrade for your %s"):format(slotName:lower()) end
        end
        if why then
          table.insert(take, { bag = bag, slot = slot, link = link, icon = icon, count = count or 1, why = why })
        end
      end
    end
  end
  return deposit, take, freeBags
end

-- Panel --------------------------------------------------------------------------------------
local panel
local refresh
local S

local function move(e)
  if C_Container and C_Container.UseContainerItem then C_Container.UseContainerItem(e.bag, e.slot)
  else UseContainerItem(e.bag, e.slot) end
end

local function build()
  S = DruidKitStyle
  panel = S.window("DruidKitBankCheck", "Bank check", "Interface\\Icons\\INV_Misc_Bag_10_Green", 400, 470)
end

local function title(e)
  local name, _, q = API.getInfo(e.link)
  return (name or "?") .. (e.count > 1 and ("  |cffffffffx" .. e.count .. "|r") or ""), q or 1
end

refresh = function()
  if not panel or not panel:IsShown() then return end
  local deposit, take, free = classify()
  panel.sub:SetText(("%d bag slot%s free"):format(free, free == 1 and "" or "s"))
  local function doAll(list) return function()
    for _, e in ipairs(list) do move(e) end
    C_Timer.After(0.6, refresh)
  end end
  S.begin(panel)

  S.header(panel, "Take out", "Interface\\Icons\\INV_Misc_Herb_10", #take, #take > 0 and "Take all" or nil, doAll(take))
  if #take == 0 then S.note(panel, "Nothing in the bank you need right now.") end
  for _, e in ipairs(take) do
    local t, q = title(e)
    S.item(panel, e.link, e.icon, q, t, (e.why:gsub("^%l", string.upper)), "Take", function() move(e); C_Timer.After(0.4, refresh) end)
  end

  S.header(panel, "Put in the bank", "Interface\\Icons\\INV_Box_02", #deposit, #deposit > 0 and "Store all" or nil, doAll(deposit))
  if not haveReagentData() then
    S.note(panel, "Open your Alchemy, First Aid and Cooking windows once so I know which herbs and cloth you use.")
  elseif #deposit == 0 then
    S.note(panel, "Your bags only hold what you're using.")
  end
  for _, e in ipairs(deposit) do
    local t, q = title(e)
    S.item(panel, e.link, e.icon, q, t, (e.why:gsub("^%l", string.upper)), "Store", function() move(e); C_Timer.After(0.4, refresh) end)
  end

  S.finish(panel)
  panel.footer:SetText("Gear to sell or equip: /dk bags")
end

-- Events -------------------------------------------------------------------------------------
local ev = CreateFrame("Frame")
for _, e in ipairs({ "PLAYER_LOGIN", "PLAYER_INTERACTION_MANAGER_FRAME_SHOW", "PLAYER_INTERACTION_MANAGER_FRAME_HIDE", "BANKFRAME_OPENED", "BANKFRAME_CLOSED", "PLAYERBANKSLOTS_CHANGED", "BAG_UPDATE_DELAYED", "TRADE_SKILL_SHOW", "TRADE_SKILL_UPDATE" }) do
  pcall(ev.RegisterEvent, ev, e)
end
local pending
ev:SetScript("OnEvent", function(_, e, a1)
  if e == "PLAYER_INTERACTION_MANAGER_FRAME_SHOW" or e == "PLAYER_INTERACTION_MANAGER_FRAME_HIDE" then
    local BANKER = Enum and Enum.PlayerInteractionType and Enum.PlayerInteractionType.Banker or 8
    if a1 ~= BANKER then return end
    e = (e == "PLAYER_INTERACTION_MANAGER_FRAME_SHOW") and "BANKFRAME_OPENED" or "BANKFRAME_CLOSED"
  end
  if e == "PLAYER_LOGIN" then
    API = DruidKitBagsAPI
    DruidKitDB = DruidKitDB or {}
    -- Drop the mixed-up lists saved before v-prof fix (Herbalism/Fishing have no recipes; First Aid had Alchemy's).
    if not DruidKitDB.reagentsFixed then
      DruidKitDB.reagents, DruidKitDB.reagentsAll, DruidKitDB.reagentsFixed = {}, {}, true
    end
    return
  end
  if not API then return end
  if e == "TRADE_SKILL_SHOW" or e == "TRADE_SKILL_UPDATE" then
    pcall(learnReagents)
  elseif e == "BANKFRAME_OPENED" then
    if not panel then build() end
    panel:ClearAllPoints()
    if BankFrame and BankFrame:IsShown() then panel:SetPoint("TOPLEFT", BankFrame, "TOPRIGHT", 4, 0)
    else panel:SetPoint("LEFT", UIParent, "CENTER", 120, 0) end
    panel:Show()
    pcall(refresh)
  elseif e == "BANKFRAME_CLOSED" then
    if panel then panel:Hide() end
  elseif panel and panel:IsShown() and not pending then
    pending = true
    C_Timer.After(0.5, function() pending = false; pcall(refresh) end)
  end
end)
