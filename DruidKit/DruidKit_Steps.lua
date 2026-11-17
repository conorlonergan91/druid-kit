-- Druid Kit: step tracker.
-- One action at a time from DruidKitRoute (generated into DruidKit_Guide.lua): accept, hand in,
-- do objectives, go somewhere, fly, train. Steps tick themselves off from quest and zone events,
-- the navigation arrow follows the current step, and the guide's own quests are accepted and
-- handed in for you (hold Shift at a quest giver to do it yourself).
-- Words carry every state; colour is only a second signal.

local DB
local steps = {}          -- flattened route: { sec = "title", ...step fields }
local titleDone = {}      -- quest titles handed in (for steps that match by name)
local arrived = {}        -- step index -> true once its spot was reached
local frame
local pos = 1
local lastArrowFor

local Y, G, W, R = "|cffffd100", "|cff9d9d9d", "|cffffffff", "|r"

local function say(m) print("|cff7fd35bDruid Kit:|r " .. m) end
local function safe(fn, ...)
  if type(fn) ~= "function" then return end
  local ok, a, b, c = pcall(fn, ...)
  if ok then return a, b, c end
end

-- Route ----------------------------------------------------------------------------------------
local function flatten()
  for k in pairs(steps) do steps[k] = nil end
  local route = DruidKitRoute
  if not route then return end
  for _, sec in ipairs(route.sections or {}) do
    for _, st in ipairs(sec.steps or {}) do
      st.sec = sec.title
      table.insert(steps, st)
    end
  end
end

-- Quest state ----------------------------------------------------------------------------------
local function logEntry(q, name)
  if q and C_QuestLog and C_QuestLog.GetLogIndexForQuestID then
    local idx = safe(C_QuestLog.GetLogIndexForQuestID, q)
    if idx and idx > 0 then return q end
  end
  local n = (C_QuestLog and C_QuestLog.GetNumQuestLogEntries and safe(C_QuestLog.GetNumQuestLogEntries)) or 0
  for i = 1, n do
    local info = safe(C_QuestLog.GetInfo, i)
    if info and not info.isHeader then
      if (q and info.questID == q) or (not q and name and info.title == name) then return info.questID end
    end
  end
end

local function turnedIn(q, name)
  if q then
    local f = (C_QuestLog and C_QuestLog.IsQuestFlaggedCompleted) or IsQuestFlaggedCompleted
    if safe(f, q) then return true end
  end
  return (not q) and name and titleDone[name] or false
end

local function objectivesDone(q, name)
  local id = logEntry(q, name)
  if not id then return false end
  if C_QuestLog and C_QuestLog.IsComplete and safe(C_QuestLog.IsComplete, id) then return true end
  local objs = C_QuestLog and C_QuestLog.GetQuestObjectives and safe(C_QuestLog.GetQuestObjectives, id)
  if type(objs) == "table" and #objs > 0 then
    for _, o in ipairs(objs) do if not o.finished then return false end end
    return true
  end
  return false
end

local function progressText(q, name)
  local id = logEntry(q, name)
  local objs = id and C_QuestLog and C_QuestLog.GetQuestObjectives and safe(C_QuestLog.GetQuestObjectives, id)
  if type(objs) ~= "table" then return end
  local parts = {}
  for _, o in ipairs(objs) do
    if o.text and o.text ~= "" then table.insert(parts, (o.finished and "done: " or "") .. o.text) end
  end
  return #parts > 0 and table.concat(parts, " · ") or nil
end

local function placeMatches(to)
  if not to then return false end
  local want = to:lower()
  for _, f in ipairs({ GetZoneText, GetSubZoneText, GetMinimapZoneText, GetRealZoneText }) do
    local t = safe(f)
    if type(t) == "string" and t ~= "" and (t:lower():find(want, 1, true) or want:find(t:lower(), 1, true)) then
      return true
    end
  end
  return false
end

local function isDone(i)
  local st = steps[i]
  if not st then return true end
  if DB.manual[i] then return true end
  local d = st["do"]
  if d == "accept" then
    return logEntry(st.q, st.name) ~= nil or turnedIn(st.q, st.name)
  elseif d == "turnin" then
    return turnedIn(st.q, st.name)
  elseif d == "complete" then
    return objectivesDone(st.q, st.name) or turnedIn(st.q, st.name)
  elseif d == "goto" then
    return arrived[i] == true or (st.to ~= nil and placeMatches(st.to))
  elseif d == "fly" or d == "hearth" then
    return placeMatches(st.to) or arrived[i] == true
  elseif d == "level" then
    return (UnitLevel("player") or 0) >= (st.level or 999)
  end
  return false   -- note, train: you tick them (train also ticks when you close the trainer)
end

-- Text -----------------------------------------------------------------------------------------
local VERB = { accept = "Accept", turnin = "Hand in", complete = "Do", ["goto"] = "Go to", fly = "Fly to",
  hearth = "Hearth to", train = "Train", level = "Level", note = "Do" }

local function mainLine(st)
  local d = st["do"]
  if d == "accept" or d == "turnin" then
    return Y .. VERB[d] .. ":" .. R .. " " .. W .. st.name .. R .. (st.npc and (G .. "  (" .. st.npc .. ")" .. R) or "")
  elseif d == "fly" or d == "hearth" then
    return Y .. VERB[d] .. R .. " " .. W .. (st.to or "?") .. R
  elseif d == "train" then
    return Y .. "Train" .. R .. " " .. W .. (st.npc or "new spells") .. R
  elseif d == "level" then
    return Y .. "Level " .. (st.level or "?") .. R .. "  " .. W .. (st.text or "") .. R
  end
  return Y .. VERB[d or "note"] .. ":" .. R .. " " .. W .. (st.text or st.name or "") .. R
end

local function detailLines(st)
  local out = {}
  if st.where then table.insert(out, "Where: " .. st.where .. (st.at and ("  (" .. st.at[2] .. ", " .. st.at[3] .. ")") or "")) end
  if st["do"] == "complete" then
    local p = progressText(st.q, st.name)
    if p then table.insert(out, "Progress: " .. p) end
  end
  if st.pick then table.insert(out, "Reward: " .. st.pick) end
  if st.tip then table.insert(out, "Tip: " .. st.tip) end
  return table.concat(out, "\n")
end

local function shortLine(st)
  local d = st["do"]
  if d == "accept" or d == "turnin" then return VERB[d] .. " " .. st.name end
  if d == "fly" or d == "hearth" then return VERB[d] .. " " .. (st.to or "") end
  if d == "level" then return "Level " .. (st.level or "") end
  if d == "train" then return "Train" end
  return st.text or st.name or ""
end

-- Arrow ----------------------------------------------------------------------------------------
local function pointArrow()
  local st = steps[pos]
  if not st or lastArrowFor == pos then return end
  lastArrowFor = pos
  if DB.arrowOff then return end
  if st.at and DruidKit_GoTo then
    DruidKit_GoTo(st.at[1], st.at[2], st.at[3], st.npc or st.text or st.name or "Next step", true)
  elseif DruidKit_NavTarget and DruidKit_NavTarget() and DruidKit_NavClear then
    DruidKit_NavClear(true)   -- an old arrow would point the wrong way
  end
end

-- Window ---------------------------------------------------------------------------------------
local function build()
  frame = CreateFrame("Frame", "DruidKitSteps", UIParent, BackdropTemplateMixin and "BackdropTemplate" or nil)
  frame:SetSize(340, 150)
  frame:SetFrameStrata("MEDIUM")
  frame:SetClampedToScreen(true)
  frame:SetMovable(true); frame:EnableMouse(true); frame:RegisterForDrag("LeftButton")
  frame:SetScript("OnDragStart", frame.StartMoving)
  frame:SetScript("OnDragStop", function(f)
    f:StopMovingOrSizing()
    local _, _, _, x, y = f:GetPoint()
    DB.stepsPos = { x, y }
  end)
  if frame.SetBackdrop then
    frame:SetBackdrop({ bgFile = "Interface\\Tooltips\\UI-Tooltip-Background",
      edgeFile = "Interface\\Tooltips\\UI-Tooltip-Border", edgeSize = 12, insets = { left = 3, right = 3, top = 3, bottom = 3 } })
    frame:SetBackdropColor(0, 0, 0, 0.8)
  end
  local p = DB.stepsPos
  frame:SetPoint("TOPRIGHT", UIParent, "TOPRIGHT", p and p[1] or -20, p and p[2] or -230)

  local function fs(size, r, g, b)
    local f = frame:CreateFontString(nil, "OVERLAY")
    f:SetFont("Fonts\\FRIZQT__.TTF", size, "OUTLINE")
    f:SetJustifyH("LEFT"); f:SetJustifyV("TOP"); f:SetWidth(320)
    if f.SetWordWrap then f:SetWordWrap(true) end
    f:SetTextColor(r, g, b)
    return f
  end
  frame.head = fs(12, 0.62, 0.62, 0.62); frame.head:SetPoint("TOPLEFT", 10, -8); frame.head:SetWidth(200)
  frame.main = fs(16, 1, 1, 1);          frame.main:SetPoint("TOPLEFT", frame.head, "BOTTOMLEFT", 0, -4)
  frame.detail = fs(13, 0.85, 0.85, 0.85); frame.detail:SetPoint("TOPLEFT", frame.main, "BOTTOMLEFT", 0, -4)
  frame.next = fs(12, 0.62, 0.62, 0.62); frame.next:SetPoint("TOPLEFT", frame.detail, "BOTTOMLEFT", 0, -6)

  local function btn(label, tip, onClick, x)
    local b = CreateFrame("Button", nil, frame, "UIPanelButtonTemplate")
    b:SetSize(56, 20); b:SetText(label)
    b:SetPoint("TOPRIGHT", frame, "TOPRIGHT", x, -5)
    b:SetScript("OnClick", onClick)
    b:SetScript("OnEnter", function(s) GameTooltip:SetOwner(s, "ANCHOR_LEFT"); GameTooltip:SetText(tip, 1, 1, 1, 1, true); GameTooltip:Show() end)
    b:SetScript("OnLeave", function() GameTooltip:Hide() end)
    return b
  end
  frame.doneBtn = btn("Done", "Mark this step done and move on.", function() DruidKit_StepDone() end, -6)
  frame.backBtn = btn("Back", "Go back one step.", function() DruidKit_StepBack() end, -64)
end

local function resize()
  local h = 16 + frame.head:GetStringHeight() + frame.main:GetStringHeight() + frame.detail:GetStringHeight()
    + frame.next:GetStringHeight() + 18
  frame:SetHeight(math.max(80, h))
end

local function draw()
  if not frame then return end
  local st = steps[pos]
  if not st then
    frame.head:SetText("Druid Kit route")
    frame.main:SetText(Y .. "Route finished." .. R .. " Say \"update\" for the next part.")
    frame.detail:SetText(""); frame.next:SetText("")
    resize()
    return
  end
  frame.head:SetText(("Step %d of %d · %s"):format(pos, #steps, st.sec or ""))
  frame.main:SetText(mainLine(st))
  frame.detail:SetText(detailLines(st))
  local nxt = {}
  for i = pos + 1, math.min(#steps, pos + 2) do table.insert(nxt, "Then: " .. shortLine(steps[i])) end
  frame.next:SetText(table.concat(nxt, "\n"))
  resize()
end

-- Advancing ------------------------------------------------------------------------------------
local function evaluate()
  if not DB then return end
  local moved = false
  while pos <= #steps and isDone(pos) do pos = pos + 1; moved = true end
  DB.routeStep = pos
  if moved then lastArrowFor = nil end
  pointArrow()
  draw()
end
DruidKit_StepsEvaluate = function() pcall(evaluate) end

function DruidKit_StepDone()
  if not steps[pos] then return end
  DB.manual[pos] = true
  pos = pos + 1
  lastArrowFor = nil
  evaluate()
end

function DruidKit_StepBack()
  if pos <= 1 then return end
  pos = pos - 1
  DB.manual[pos] = nil
  arrived[pos] = nil
  DB.routeStep = pos
  lastArrowFor = nil
  pointArrow(); draw()
end

function DruidKit_ToggleSteps(show)
  if not frame then build() end
  if show == nil then show = not frame:IsShown() end
  DB.stepsHidden = not show
  if show then frame:Show(); evaluate() else frame:Hide() end
end

-- The Now tab and the doc use this list too.
function DruidKit_RouteSteps() return steps, pos end

-- Automatic quest accept / hand-in ------------------------------------------------------------
-- Only for quests in the route from the current step onward; Shift held = you do it yourself.
local function wanted(kind, q, name)
  for i = math.max(1, pos - 3), #steps do
    local st = steps[i]
    if st["do"] == kind and ((q and st.q == q) or (name and st.name == name and (not st.q or not q))) then return st end
  end
end

local function autoOn() return DB and DB.autoQuests ~= false and not IsShiftKeyDown() end

-- Returns true when the quest was handed in.
local function pickReward(st)
  local n = safe(GetNumQuestChoices) or 0
  if n <= 1 then safe(GetQuestReward, n); return true end
  if not (st and st.pick) then
    say("pick your reward yourself (the guide has no choice for this one).")
    return false
  end
  for i = 1, n do
    local itemName = safe(GetQuestItemInfo, "choice", i)
    if itemName == st.pick then safe(GetQuestReward, i); say("took " .. st.pick .. "."); return true end
  end
  say("couldn't find " .. st.pick .. " in the rewards: pick yourself.")
  return false
end

local function gossipQuests()
  if not (C_GossipInfo and autoOn()) then return end
  for _, q in ipairs(safe(C_GossipInfo.GetActiveQuests) or {}) do
    if q.isComplete and wanted("turnin", q.questID, q.title) then safe(C_GossipInfo.SelectActiveQuest, q.questID); return end
  end
  for _, q in ipairs(safe(C_GossipInfo.GetAvailableQuests) or {}) do
    if wanted("accept", q.questID, q.title) then safe(C_GossipInfo.SelectAvailableQuest, q.questID); return end
  end
end

local function greetingQuests()
  if not autoOn() then return end
  for i = 1, (safe(GetNumActiveQuests) or 0) do
    local title, isComplete = safe(GetActiveTitle, i)
    if isComplete and wanted("turnin", nil, title) then safe(SelectActiveQuest, i); return end
  end
  for i = 1, (safe(GetNumAvailableQuests) or 0) do
    if wanted("accept", nil, safe(GetAvailableTitle, i)) then safe(SelectAvailableQuest, i); return end
  end
end

-- Events ---------------------------------------------------------------------------------------
local ev = CreateFrame("Frame")
for _, e in ipairs({ "PLAYER_LOGIN", "QUEST_LOG_UPDATE", "QUEST_ACCEPTED", "QUEST_TURNED_IN", "QUEST_REMOVED",
  "ZONE_CHANGED", "ZONE_CHANGED_NEW_AREA", "ZONE_CHANGED_INDOORS", "PLAYER_LEVEL_UP", "TRAINER_CLOSED",
  "QUEST_DETAIL", "QUEST_PROGRESS", "QUEST_COMPLETE", "GOSSIP_SHOW", "QUEST_GREETING" }) do
  pcall(ev.RegisterEvent, ev, e)
end

local pending = false
local function soon()
  if pending then return end
  pending = true
  C_Timer.After(0.3, function() pending = false; pcall(evaluate) end)
end

ev:SetScript("OnEvent", function(_, e, a1)
  if e == "PLAYER_LOGIN" then
    DruidKitDB = DruidKitDB or {}
    DB = DruidKitDB
    DB.manual = DB.manual or {}
    DB.titleDone = DB.titleDone or {}
    titleDone = DB.titleDone
    flatten()
    local id = DruidKitRoute and DruidKitRoute.id
    if DB.routeId ~= id then
      DB.routeId = id; DB.routeStep = 1; DB.manual = {}
    end
    pos = DB.routeStep or 1
    DruidKit_ToggleSteps(not DB.stepsHidden and #steps > 0)
    return
  end
  if not DB then return end
  if e == "QUEST_TURNED_IN" then
    local t = a1 and C_QuestLog and C_QuestLog.GetTitleForQuestID and safe(C_QuestLog.GetTitleForQuestID, a1)
    if t then titleDone[t] = true end
    soon()
  elseif e == "TRAINER_CLOSED" then
    local st = steps[pos]
    if st and st["do"] == "train" then DB.manual[pos] = true end
    soon()
  elseif e == "QUEST_DETAIL" then
    if autoOn() then
      local q = safe(GetQuestID)
      if wanted("accept", q, safe(GetTitleText)) then safe(AcceptQuest); soon() end
    end
  elseif e == "QUEST_PROGRESS" then
    if autoOn() and safe(IsQuestCompletable) then
      local q = safe(GetQuestID)
      if wanted("turnin", q, safe(GetTitleText)) then safe(CompleteQuest) end
    end
  elseif e == "QUEST_COMPLETE" then
    if autoOn() then
      local q = safe(GetQuestID)
      local st = wanted("turnin", q, safe(GetTitleText))
      if st and pickReward(st) and st.name and not st.q then titleDone[st.name] = true end
    end
  elseif e == "GOSSIP_SHOW" then
    gossipQuests()
  elseif e == "QUEST_GREETING" then
    greetingQuests()
  else
    soon()
  end
end)

-- Arrival at the current step's spot (from the navigation arrow).
DruidKit_OnArrive = function()
  local st = steps[pos]
  if st and st.at and (st["do"] == "goto" or st["do"] == "fly" or st["do"] == "hearth") then
    arrived[pos] = true
    soon()
  end
end

-- Keep progress text fresh while you work on a "Do" step.
local tick = 0
ev:SetScript("OnUpdate", function(_, el)
  tick = tick + el
  if tick < 2 then return end
  tick = 0
  if frame and frame:IsShown() and steps[pos] and steps[pos]["do"] == "complete" then pcall(draw) end
end)

-- /dk steps | /dk steps reset | /dk auto
function DruidKit_StepsCommand(arg)
  arg = (arg or ""):lower()
  if arg == "reset" then
    DB.manual = {}; pos = 1; DB.routeStep = 1; arrived = {}; lastArrowFor = nil
    DruidKit_ToggleSteps(true)
    say("route restarted: finished steps skip themselves.")
  elseif arg == "auto" then
    DB.autoQuests = DB.autoQuests == false
    say("automatic quest accept and hand-in " .. (DB.autoQuests == false and "OFF." or "ON (hold Shift to do it yourself)."))
  elseif arg == "arrow" then
    DB.arrowOff = not DB.arrowOff
    say("route arrow " .. (DB.arrowOff and "OFF." or "ON."))
    lastArrowFor = nil; pointArrow()
  else
    DruidKit_ToggleSteps()
  end
end
