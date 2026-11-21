-- Druid Kit: dungeon quests (/dk dq), quest share helper for groups (/dk share), quest XP on the XP bar.
-- Data: DruidKitDungeonData (tools/dungeon_data.py). XP: Questie's QuestXP module when it is loaded, else the data.

local S = DruidKitStyle
local LEAF, GREY, GOLD, RED, R = "|cff7fd35b", "|cff9d9d9d", "|cffffd100", "|cffff6060", "|r"
local function say(msg) print("|cffff7d0aDruid Kit:|r " .. msg) end
local function pass(ok, ...) if ok then return ... end end
local function safe(fn, ...)
  if not fn then return nil end
  return pass(pcall(fn, ...))
end
local function plain(v) return not (issecretvalue and issecretvalue(v)) end

-- Quest state ------------------------------------------------------------------------------------
local function completed(id)
  if C_QuestLog and C_QuestLog.IsQuestFlaggedCompleted then return safe(C_QuestLog.IsQuestFlaggedCompleted, id) == true end
  return IsQuestFlaggedCompleted and safe(IsQuestFlaggedCompleted, id) == true or false
end

-- questID -> { index = log index, complete = bool } for the quests in your log
local function questLog()
  local out = {}
  local n = (C_QuestLog and C_QuestLog.GetNumQuestLogEntries and safe(C_QuestLog.GetNumQuestLogEntries))
    or (GetNumQuestLogEntries and safe(GetNumQuestLogEntries)) or 0
  for i = 1, n do
    if C_QuestLog and C_QuestLog.GetInfo then
      local info = safe(C_QuestLog.GetInfo, i)
      if info and not info.isHeader and info.questID then
        out[info.questID] = { index = i, complete = info.isComplete == 1 or info.isComplete == true or
          (C_QuestLog.IsComplete and safe(C_QuestLog.IsComplete, info.questID) == true) }
      end
    elseif GetQuestLogTitle then
      local _, _, _, isHeader, _, isComplete, _, questID = safe(GetQuestLogTitle, i)
      if questID and not isHeader then out[questID] = { index = i, complete = isComplete == 1 or isComplete == true } end
    end
  end
  return out
end

local QDATA = {}   -- questID -> data row, dungeon name
for _, d in ipairs(DruidKitDungeonData or {}) do
  for _, q in ipairs(d.quests) do q.dungeon = d.name; QDATA[q.id] = q end
end

-- Quest XP for you now: Questie's own number (with its level cut) when Questie is loaded, else the data.
local function questXP(id)
  if QuestieLoader and QuestieLoader.ImportModule then
    local ok, mod = pcall(QuestieLoader.ImportModule, QuestieLoader, "QuestXP")
    if ok and mod and mod.GetQuestLogRewardXP then
      local xp = safe(mod.GetQuestLogRewardXP, mod, id)
      if xp and xp > 0 then return xp end
    end
  end
  local q = QDATA[id]
  if not q or not q.xp then return 0 end
  local lvl = UnitLevel("player") or 1
  local mult = math.min(10, math.max(1, 2 * ((q.level or lvl) - lvl) + 20))
  return math.floor(q.xp * mult / 10)
end

local function status(q, log)
  if completed(q.id) then return "done" end
  if log[q.id] then return log[q.id].complete and "ready" or "active" end
  local lvl = UnitLevel("player") or 1
  if (q.min or 1) > lvl then return "locked", "needs level " .. q.min end
  if q.pre and #q.pre > 0 then
    local any = false
    for _, p in ipairs(q.pre) do if completed(p) then any = true end end
    if not any then
      local pq = QDATA[q.pre[1]]
      return "locked", "first: " .. (pq and pq.name or ("quest " .. q.pre[1]))
    end
  end
  for _, p in ipairs(q.preAll or {}) do
    if not completed(p) then
      local pq = QDATA[p]
      return "locked", "first: " .. (pq and pq.name or ("quest " .. p))
    end
  end
  return "available"
end

-- /dk dq: dungeon quest list -----------------------------------------------------------------------
local dq
local LABEL = { done = GREY .. "done" .. R, ready = LEAF .. "ready to hand in" .. R, active = GOLD .. "in your log" .. R,
  available = LEAF .. "available" .. R, locked = RED .. "locked" .. R }

local function drawDQ()
  if not S then return end
  dq = dq or S.window("DruidKitDungeonQuests", "Dungeon quests", "Interface\\Icons\\INV_Misc_Book_09", 470, 520)
  local log = questLog()
  local lvl = UnitLevel("player") or 1
  S.begin(dq)
  local shown, total = 0, 0
  for _, d in ipairs(DruidKitDungeonData or {}) do
    local lo, todo = 99, 0
    for _, q in ipairs(d.quests) do
      lo = math.min(lo, q.min or 99)
      if status(q, log) ~= "done" then todo = todo + 1 end
    end
    -- dungeons near your level with something left to do
    if todo > 0 and lo <= lvl + 6 and lo >= lvl - 12 then
      shown = shown + 1
      local xpLeft = 0
      for _, q in ipairs(d.quests) do if status(q, log) ~= "done" then xpLeft = xpLeft + questXP(q.id) end end
      total = total + xpLeft
      S.header(dq, d.name, "Interface\\Icons\\INV_Misc_Map_01", todo)
      for _, q in ipairs(d.quests) do
        local st, why = status(q, log)
        if st ~= "done" then
          local where = q.at and (q.giver and (q.giver .. ", ") or "") .. q.at[1] .. " " .. q.at[2] .. ", " .. q.at[3]
            or (q.giver or "inside the dungeon")
          local detail = LABEL[st] .. (why and (GREY .. " (" .. why .. ")" .. R) or "") .. GREY .. "  ·  "
            .. questXP(q.id) .. " XP  ·  " .. where .. R
          local btn, onClick
          if q.at and (st == "available" or st == "locked") and DruidKit_GoTo then
            btn, onClick = "Go", function() DruidKit_GoTo(q.at[1], q.at[2], q.at[3], q.name .. " (" .. (q.giver or "quest") .. ")") end
          end
          S.item(dq, nil, "Interface\\GossipFrame\\AvailableQuestIcon", 1, q.name, detail, btn, onClick)
        end
      end
    end
  end
  if shown == 0 then S.note(dq, "No dungeon quests left near your level.") end
  S.finish(dq)
  dq.sub:SetText(("Level %d · %s%d XP|r of dungeon quests left near your level"):format(lvl, LEAF, total))
  dq.footer:SetText("Go: arrow to the quest giver. In a group: /dk share")
  dq:Show()
end
DruidKit_DungeonQuests = drawDQ

-- Quest share helper -------------------------------------------------------------------------------
local share
local function partyUnits()
  local units = {}
  if IsInRaid and safe(IsInRaid) then return units end
  for i = 1, 4 do
    local u = "party" .. i
    if UnitExists and safe(UnitExists, u) then table.insert(units, u) end
  end
  return units
end

local function unitOnQuest(unit, id, index)
  if C_QuestLog and C_QuestLog.IsUnitOnQuest then
    local v = safe(C_QuestLog.IsUnitOnQuest, unit, id)
    if v ~= nil then return v == true end
  end
  if IsUnitOnQuest and index then return safe(IsUnitOnQuest, index, unit) == 1 or safe(IsUnitOnQuest, index, unit) == true end
  return nil   -- unknown
end

local function pushable(id, index)
  if C_QuestLog and C_QuestLog.IsPushableQuest then return safe(C_QuestLog.IsPushableQuest, id) == true end
  if GetQuestLogPushable and index then
    if SelectQuestLogEntry then safe(SelectQuestLogEntry, index) end
    return safe(GetQuestLogPushable) == 1 or safe(GetQuestLogPushable) == true
  end
  return true
end

local function pushQuest(id, index)
  if C_QuestLog and C_QuestLog.SetSelectedQuest then safe(C_QuestLog.SetSelectedQuest, id) end
  if SelectQuestLogEntry and index then safe(SelectQuestLogEntry, index) end
  if QuestLogPushQuest then safe(QuestLogPushQuest) end
end

-- dungeon quests in your log that someone in the party does not have: { {id, index, name, missing = {names}} }
local function shareList()
  local units = partyUnits()
  if #units == 0 then return {}, 0 end
  local out = {}
  for id, e in pairs(questLog()) do
    local q = QDATA[id]
    if q and pushable(id, e.index) then
      local missing = {}
      for _, u in ipairs(units) do
        if unitOnQuest(u, id, e.index) == false then
          local n = UnitName(u)
          table.insert(missing, plain(n) and n or "?")
        end
      end
      if #missing > 0 then table.insert(out, { id = id, index = e.index, name = q.name, dungeon = q.dungeon, missing = missing }) end
    end
  end
  table.sort(out, function(a, b) return a.dungeon == b.dungeon and a.name < b.name or a.dungeon < b.dungeon end)
  return out, #units
end

local function drawShare(quiet)
  if not S then return end
  local list, members = shareList()
  if quiet and #list == 0 then if share then share:Hide() end return end
  share = share or S.window("DruidKitQuestShare", "Share dungeon quests", "Interface\\Icons\\INV_Letter_15", 420, 380)
  S.begin(share)
  if members == 0 then
    S.note(share, "You are not in a group.")
  elseif #list == 0 then
    S.note(share, "Everyone in your group has your dungeon quests (or the game can't share them).")
  else
    S.header(share, "Others don't have these", "Interface\\Icons\\INV_Letter_15", #list, "Share all", function()
      for i, e in ipairs(list) do C_Timer.After((i - 1) * 0.6, function() pushQuest(e.id, e.index) end) end
      say(("sharing %d quest(s) with your group."):format(#list))
    end)
    for _, e in ipairs(list) do
      S.item(share, nil, "Interface\\GossipFrame\\AvailableQuestIcon", 1, e.name,
        GREY .. e.dungeon .. " · missing: " .. table.concat(e.missing, ", ") .. R, "Share", function() pushQuest(e.id, e.index) end)
    end
  end
  S.finish(share)
  share.sub:SetText("Your dungeon quests and who in the group still needs them")
  share.footer:SetText("Quests that others share with you tick their accept steps by themselves.")
  share:Show()
end
DruidKit_QuestShare = drawShare

-- Quest XP on the XP bar ---------------------------------------------------------------------------
local xpText
local function readyXP()
  local sum, n = 0, 0
  for id, e in pairs(questLog()) do
    if e.complete then
      local xp = questXP(id)
      if xp > 0 then sum = sum + xp; n = n + 1 end
    end
  end
  return sum, n
end

local function drawXP()
  local bar = MainMenuExpBar or (MainStatusTrackingBarContainer) or nil
  if DruidKitDB and DruidKitDB.questXPBar == false then if xpText then xpText:Hide() end return end
  local sum, n = readyXP()
  if not xpText then
    xpText = CreateFrame("Frame", "DruidKitQuestXP", UIParent)
    xpText:SetSize(300, 16)
    xpText.t = xpText:CreateFontString(nil, "OVERLAY", "GameFontNormalSmall")
    xpText.t:SetAllPoints()
    if bar then xpText:SetPoint("BOTTOM", bar, "TOP", 0, 2) elseif DruidKitPos then DruidKitPos.place(xpText, "questxp") end
  end
  if n == 0 then xpText:Hide() return end
  local cur, max = UnitXP("player") or 0, UnitXPMax("player") or 1
  if not (plain(cur) and plain(max)) or max == 0 then xpText:Hide() return end
  local lvl = UnitLevel("player") or 0
  local after = lvl + (cur + sum) / max
  xpText.t:SetText(("%sQuests to hand in: %d|r  ·  +%d XP  ·  level %.1f after"):format(LEAF, n, sum, after))
  xpText:Show()
end
DruidKit_QuestXPBar = drawXP

-- Events and commands ------------------------------------------------------------------------------
local ev = CreateFrame("Frame")
for _, e in ipairs({ "PLAYER_LOGIN", "QUEST_LOG_UPDATE", "PLAYER_XP_UPDATE", "PLAYER_LEVEL_UP", "GROUP_ROSTER_UPDATE" }) do
  pcall(ev.RegisterEvent, ev, e)
end
local lastAuto, groupSize, drawPending = 0, 0, false
ev:SetScript("OnEvent", function(_, e)
  if e == "GROUP_ROSTER_UPDATE" then
    -- someone joined: offer to share (once a minute at most), only when there is something to share
    local n = #partyUnits()
    local now = GetTime and GetTime() or 0
    if n > groupSize and now - lastAuto > 60 and not (DruidKitDB and DruidKitDB.shareAuto == false) then
      lastAuto = now
      C_Timer.After(3, function() pcall(drawShare, true) end)   -- party data needs a moment
    end
    groupSize = n
    return
  end
  if drawPending then return end
  drawPending = true
  C_Timer.After(0.5, function()
    drawPending = false
    pcall(drawXP)
    if dq and dq:IsShown() then pcall(drawDQ) end
  end)
end)

do
  local prev = DruidKit_HelperCommand
  DruidKit_HelperCommand = function(cmd, rest)
    rest = (rest or ""):lower()
    if cmd == "dq" or cmd == "dungeons" then pcall(drawDQ); return true end
    if cmd == "share" then
      if rest == "off" or rest == "on" then
        DruidKitDB.shareAuto = rest == "on"
        say("Share window when someone joins your group: " .. rest .. ".")
      else pcall(drawShare) end
      return true
    end
    if cmd == "questxp" then
      DruidKitDB.questXPBar = rest ~= "off"
      say("Quest XP over the XP bar: " .. (DruidKitDB.questXPBar and "on" or "off") .. ".")
      pcall(drawXP)
      return true
    end
    return prev and prev(cmd, rest)
  end
end
