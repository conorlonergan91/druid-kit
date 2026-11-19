-- Druid Kit: step tracker.
-- One action at a time from DruidKitRoute (generated into DruidKit_Guide.lua): accept, hand in,
-- do objectives, go somewhere, fly, train, learn a flight path (fp), set the hearthstone (home). Steps tick themselves off from quest and zone events,
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
BINDING_NAME_DRUIDKIT_STEPS = "Show / hide route steps and arrow"

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

-- The quest's own "what to do" text from your log (e.g. "use the banner you found"), so the step
-- explains how, not just what.
local function questHowText(q, name)
  local id = logEntry(q, name)
  if not id or not GetQuestLogQuestText then return end
  local idx = C_QuestLog and C_QuestLog.GetLogIndexForQuestID and safe(C_QuestLog.GetLogIndexForQuestID, id)
  if not idx or idx < 1 then return end
  local prev = GetQuestLogSelection and safe(GetQuestLogSelection)
  safe(SelectQuestLogEntry, idx)
  local _, objectives = safe(GetQuestLogQuestText)
  if prev and prev > 0 then safe(SelectQuestLogEntry, prev) end
  if type(objectives) ~= "string" or objectives == "" then return end
  objectives = objectives:gsub("%s+", " ")
  if #objectives > 160 then objectives = objectives:sub(1, 157):match("^(.*)%s") .. "..." end
  return objectives
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

-- Flight paths and hearthstone ----------------------------------------------------------------
-- Known flight paths come from the flight map (ClaudeProgress records them); the hearth from GetBindLocation.
local function sameName(a, b)
  if type(a) ~= "string" or type(b) ~= "string" or a == "" or b == "" then return false end
  a, b = a:lower(), b:lower()
  return a:find(b, 1, true) ~= nil or b:find(a, 1, true) ~= nil
end

local function homeName() return safe(GetBindLocation) end

local function knownFlights()
  local db = ClaudeProgressDB and ClaudeProgressDB.flights
  if type(db) ~= "table" then return nil end
  local key = (safe(UnitName, "player") or "") .. "-" .. (safe(GetRealmName) or "")
  return db[key]
end

local function knowsFlight(to)
  local k = knownFlights()
  if not k then return nil end            -- unknown until you open a flight map once
  for name in pairs(k) do
    if sameName(name:match("^([^,]+)") or name, to) then return true end
  end
  return false
end

local function isDone(i)
  local st = steps[i]
  if not st then return true end
  if DB.manual[i] then return true end
  local key = st.q or st.name
  if key and DB.skipQ[key] then return true end
  local d = st["do"]
  -- A quest the route passed while you were further on (catch-up) stays behind unless it's in your log.
  if st.q and DB.passedQ and DB.passedQ[st.q] and (d == "accept" or d == "complete" or d == "turnin")
    and not logEntry(st.q, st.name) then return true end
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
  elseif d == "home" then
    return sameName(homeName(), st.to)
  elseif d == "fp" then
    return knowsFlight(st.to) == true
  elseif d == "abandon" then
    for _, q in ipairs(st.qs or { st.q }) do
      if logEntry(q) then return false end
    end
    return true
  end
  return false   -- note, train: you tick them (train also ticks when you close the trainer)
end

-- Bags: when they fill up, name the nearest vendor (DruidKitVendors, generated from the quest data) ---------
local BAGS_LOW = 3
local function bagsFree()
  local free = 0
  for bag = 0, 4 do
    free = free + ((C_Container and C_Container.GetContainerNumFreeSlots and safe(C_Container.GetContainerNumFreeSlots, bag))
      or (GetContainerNumFreeSlots and safe(GetContainerNumFreeSlots, bag)) or 0)
  end
  return free
end

local function nearestVendor()
  local list = DruidKitVendors
  if type(list) ~= "table" or not C_Map or not C_Map.GetBestMapForUnit then return end
  local map = safe(C_Map.GetBestMapForUnit, "player")
  local p = map and safe(C_Map.GetPlayerMapPosition, map, "player")
  if not p then return end
  local px, py = p:GetXY()
  local w, h = 1000, 667
  if DruidKit_MapYards then
    local a, b = DruidKit_MapYards(map)
    if a then w, h = a, b end
  end
  local best, bd
  for _, v in ipairs(list) do
    if DruidKit_FindMap and DruidKit_FindMap(v[1]) == map then
      local d = math.sqrt(((v[2] / 100 - px) * w) ^ 2 + ((v[3] / 100 - py) * h) ^ 2)
      if not bd or d < bd then best, bd = v, d end
    end
  end
  return best, bd
end

local lastBagSay = -1000
local customNav = false   -- the arrow points somewhere you chose (vendor, Go on another step) until you arrive
local view                -- step being previewed with Prev/Next (nil = the current step)
local function bagLine()
  if DB and DB.vendorPrompt == false then return nil end
  local free = bagsFree()
  if free > BAGS_LOW then return nil end
  local v, d = nearestVendor()
  local head = free == 0 and "BAGS FULL." or ("BAGS: " .. free .. " free.")
  if not v then return head .. " No vendor known in this zone: sell at the next town." end
  return ("%s Nearest vendor: %s%s, %d yards%s. The Vendor button sets the arrow."):format(head, v[4],
    v[5] ~= "" and (" (" .. v[5] .. ")") or "", math.floor(d + 0.5), v[6] and ", repairs too" or "")
end

-- Projected vs actual ------------------------------------------------------------------------
-- DB.cur tracks the step you're on: play time, deaths and XP. When it ends (done, skipped or
-- ticked) a line goes into DB.stepLog, which the next "update" reads to re-plan.
local function xpNow()
  return (safe(UnitLevel, "player") or 1), (safe(UnitXP, "player") or 0), (safe(UnitXPMax, "player") or 1)
end

local function startStats()
  local lv, xp, mx = xpNow()
  DB.cur = { i = pos, secs = 0, deaths = 0, lv = lv, xp = xp, mx = mx, trail = {} }
end

-- Breadcrumbs: where you actually walked during a step (map id, x, y every few yards). The planner reads
-- them to learn real paths (cave entrances, ramps) and turn them into waypoints for next time.
local function recordTrail()
  local c = DB.cur
  if not c or c.i ~= pos or not C_Map or not C_Map.GetBestMapForUnit then return end
  local m = safe(C_Map.GetBestMapForUnit, "player")
  local p = m and safe(C_Map.GetPlayerMapPosition, m, "player")
  if not p then return end
  local x, y = p:GetXY()
  if not x then return end
  c.trail = c.trail or {}
  local last = c.trail[#c.trail]
  if last and last[1] == m and math.abs(last[2] - x) + math.abs(last[3] - y) < 0.004 then return end
  if #c.trail >= 240 then return end
  table.insert(c.trail, { m, math.floor(x * 1000 + 0.5) / 1000, math.floor(y * 1000 + 0.5) / 1000 })
end

local function trailString(t)
  if not t or #t == 0 then return nil end
  local out = {}
  for _, p in ipairs(t) do table.insert(out, ("%d:%.3f,%.3f"):format(p[1], p[2], p[3])) end
  return table.concat(out, ";")
end

local function xpGained(c)
  local lv, xp = xpNow()
  if lv == c.lv then return xp - c.xp end
  return (c.mx - c.xp) + xp      -- crossed a level (close enough for one step)
end

local function logStep(i, how)
  local st, c = steps[i], DB.cur
  if not st then return end
  local mine = c and c.i == i
  table.insert(DB.stepLog, { route = DruidKitRoute and DruidKitRoute.id, i = i, ["do"] = st["do"], q = st.q,
    name = st.name or st.text, est = st.est, secs = mine and math.floor(c.secs) or 0,
    deaths = mine and c.deaths or 0, xp = mine and xpGained(c) or 0, lv = (xpNow()),
    how = how, at = date and date("%Y-%m-%d %H:%M"), trail = mine and trailString(c.trail) or nil,
    target = st.at and (st.at[1] .. ":" .. st.at[2] .. "," .. st.at[3]) or nil })
  while #DB.stepLog > 400 do table.remove(DB.stepLog, 1) end
  local n = #DB.stepLog
  if n > 80 and DB.stepLog[n - 80] then DB.stepLog[n - 80].trail = nil end   -- keep trails for the last 80 steps
end

local function clock(secs)
  secs = math.floor(secs or 0)
  return ("%d:%02d"):format(secs / 60, secs % 60)
end

-- Struggling = 2+ deaths on this step, or well over the projected time.
local function struggling(st)
  local c = DB.cur
  if not c or c.i ~= pos then return false end
  if c.deaths >= 2 then return true end
  local est = (st.est or 0) * 60
  return est > 0 and c.secs > math.max(est * 2.5, est + 600)
end

local function adviceLine(st)
  if st["do"] ~= "complete" and st["do"] ~= "turnin" then return nil end
  if struggling(st) then
    if st.party then
      return Y .. "Struggling:" .. R .. " group up. Type " .. W .. "/4 LFG " .. (st.name or "this quest") .. R
        .. " (kills count for everyone). Or press " .. W .. "Skip" .. R .. ": the next update decides drop or come back."
    end
    return Y .. "Struggling:" .. R .. " press " .. W .. "Skip" .. R
      .. " to leave it for now. The next update decides whether to drop it or come back stronger."
  end
  if st.party then
    return G .. "Tip: others nearby on this quest? Group up: kills count for everyone." .. R
  end
end

-- Text -----------------------------------------------------------------------------------------
local VERB = { accept = "Accept", turnin = "Hand in", complete = "Do", ["goto"] = "Go to", fly = "Fly to",
  hearth = "Hearth to", train = "Train", level = "Level", note = "Do", fp = "Learn flight path", home = "Set hearth",
  abandon = "Abandon" }

local function mainLine(st)
  local d = st["do"]
  if d == "accept" or d == "turnin" then
    return Y .. VERB[d] .. ":" .. R .. " " .. W .. st.name .. R .. (st.npc and (G .. "  (" .. st.npc .. ")" .. R) or "")
  elseif d == "fly" or d == "hearth" then
    return Y .. VERB[d] .. R .. " " .. W .. (st.to or "?") .. R
  elseif d == "fp" or d == "home" then
    return Y .. VERB[d] .. ":" .. R .. " " .. W .. (st.to or "?") .. R .. (st.npc and (G .. "  (" .. st.npc .. ")" .. R) or "")
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
  if st.how then table.insert(out, "How: " .. st.how) end
  if st["do"] == "complete" then
    local p = progressText(st.q, st.name)
    if p then table.insert(out, "Progress: " .. p) end
    local how = not st.how and questHowText(st.q, st.name)
    if how then table.insert(out, "Quest says: " .. how) end
  end
  if st.pick then table.insert(out, "Reward: " .. st.pick) end
  if st["do"] == "hearth" then
    local h = homeName()
    if h and h ~= "" and not sameName(h, st.to) then
      table.insert(out, "WARNING: your hearth is set to " .. h .. ", not " .. (st.to or "?") .. ". Walk or fly there instead, then press Done.")
    end
  elseif st["do"] == "fly" and knowsFlight(st.to) == false then
    table.insert(out, "WARNING: you have not learned the " .. (st.to or "?") .. " flight path. Walk there instead, then press Done.")
  end
  if st.tip then table.insert(out, "Tip: " .. st.tip) end
  local bl = bagLine()
  if bl then table.insert(out, bl) end
  local starters = DruidKit_QuestStarters and DruidKit_QuestStarters() or {}
  if #starters > 0 then
    local names = {}
    for i = 1, math.min(2, #starters) do names[i] = starters[i].name end
    table.insert(out, "QUEST TO START in your bags: " .. table.concat(names, ", ")
      .. (#starters > 2 and (" +" .. (#starters - 2)) or "") .. ". Right-click it in your bags.")
  end
  return table.concat(out, "\n")
end

local shortLineFull
local function clip(t, n)
  if not t or #t <= n then return t end
  local cut = t:sub(1, n):match("^(.*)[%s,;:]") or t:sub(1, n)
  return cut .. "..."
end

local function shortLine(st)
  return clip(shortLineFull(st), 58)
end

shortLineFull = function(st)
  local d = st["do"]
  if d == "accept" or d == "turnin" then return VERB[d] .. " " .. st.name end
  if d == "fly" or d == "hearth" or d == "fp" or d == "home" then return VERB[d] .. " " .. (st.to or "") end
  if d == "level" then return "Level " .. (st.level or "") end
  if d == "train" then return "Train" end
  return st.text or st.name or ""
end

-- Arrow ----------------------------------------------------------------------------------------
-- A step can list waypoints on the way ("via": cave entrance, ramp, bridge). The arrow takes them in
-- order, then the step's own spot. viaAt[pos] = how many waypoints are already reached.
local viaAt = {}
local function nextVia(st)
  local n = viaAt[pos] or 0
  return st.via and st.via[n + 1], n
end

local function pointArrow()
  local st = steps[pos]
  if not st or lastArrowFor == pos or customNav then return end
  lastArrowFor = pos
  if DB.arrowOff then return end
  local v, n = nextVia(st)
  local final = st.npc or st.text or st.name or "Next step"
  if v and DruidKit_GoTo then
    DruidKit_GoTo(v[1], v[2], v[3], ("Way %d/%d: %s  >  %s"):format(n + 1, #st.via, v[4] or "waypoint", final), true)
  elseif st.at and DruidKit_GoTo then
    DruidKit_GoTo(st.at[1], st.at[2], st.at[3], final, true)
  elseif DruidKit_GoTo and (function()
      -- No spot on this step (a walk, a boat, a note): point at the next step that has one.
      for j = pos + 1, math.min(#steps, pos + 4) do
        local nx = steps[j]
        if nx.at then
          DruidKit_GoTo(nx.at[1], nx.at[2], nx.at[3], "Next: " .. (nx.npc or nx.text or nx.name or nx.to or "step"), true)
          return true
        end
      end
    end)() then
    return
  elseif DruidKit_NavTarget and DruidKit_NavTarget() and DruidKit_NavClear then
    DruidKit_NavClear(true)   -- an old arrow would point the wrong way
  end
end

-- Window ---------------------------------------------------------------------------------------
-- Layout, top to bottom: header row (step count + section on the left, time/deaths on the right),
-- the action in large text, its details, the next two steps, then a row of buttons.
local WIDTH, PAD = 380, 10

local function build()
  frame = CreateFrame("Frame", "DruidKitSteps", UIParent, BackdropTemplateMixin and "BackdropTemplate" or nil)
  frame:SetSize(WIDTH, 160)
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
    frame:SetBackdropColor(0, 0, 0, 0.85)
  end
  local p = DB.stepsPos
  frame:SetPoint("TOPRIGHT", UIParent, "TOPRIGHT", p and p[1] or -20, p and p[2] or -230)

  local function fs(size, r, g, b, width, justify)
    local f = frame:CreateFontString(nil, "OVERLAY")
    f:SetFont("Fonts\\FRIZQT__.TTF", size, "OUTLINE")
    f:SetJustifyH(justify or "LEFT"); f:SetJustifyV("TOP"); f:SetWidth(width or (WIDTH - 2 * PAD))
    if f.SetWordWrap then f:SetWordWrap(true) end
    f:SetTextColor(r, g, b)
    return f
  end
  frame.head = fs(13, 0.75, 0.75, 0.75, WIDTH - 2 * PAD - 110); frame.head:SetPoint("TOPLEFT", PAD, -8)
  if frame.head.SetWordWrap then frame.head:SetWordWrap(false) end
  frame.stats = fs(13, 0.75, 0.75, 0.75, 110, "RIGHT"); frame.stats:SetPoint("TOPRIGHT", -PAD, -8)
  frame.main = fs(16, 1, 1, 1);           frame.main:SetPoint("TOPLEFT", frame.head, "BOTTOMLEFT", 0, -6)
  frame.detail = fs(13, 0.9, 0.9, 0.9); frame.detail:SetPoint("TOPLEFT", frame.main, "BOTTOMLEFT", 0, -4)
  frame.next = fs(13, 0.75, 0.75, 0.75);  frame.next:SetPoint("TOPLEFT", frame.detail, "BOTTOMLEFT", 0, -6)

  local x, row = PAD, 32
  local function btn(label, tip, onClick)
    local b = CreateFrame("Button", nil, frame, "UIPanelButtonTemplate")
    b:SetSize(64, 20); b:SetText(label)
    b:SetPoint("BOTTOMLEFT", frame, "BOTTOMLEFT", x, row)
    x = x + 68
    b:SetScript("OnClick", onClick)
    b:SetScript("OnEnter", function(s) GameTooltip:SetOwner(s, "ANCHOR_TOP"); GameTooltip:SetText(tip, 1, 1, 1, 1, true); GameTooltip:Show() end)
    b:SetScript("OnLeave", function() GameTooltip:Hide() end)
    return b
  end
  frame.backBtn = btn("Back", "Go back one step.", function() DruidKit_StepBack() end)
  frame.doneBtn = btn("Done", "Mark this step done and move on.", function() DruidKit_StepDone() end)
  frame.skipBtn = btn("Skip", "Leave this quest for now (dying a lot, or no group). The next update decides: drop it or come back later.", function() DruidKit_StepSkip() end)
  frame.keysBtn = btn("Keys", "Every key you have: forms, caster, Bear, Cat, Prowl and Druid Kit keys.", function()
    if DruidKit_ShowKeymap then DruidKit_ShowKeymap() end
  end)
  frame.hideBtn = btn("Hide", "Hide the steps and the arrow. Alt+N or the Route button brings them back.", function() DruidKit_ToggleSteps(false) end)
  frame.hideBtn:ClearAllPoints(); frame.hideBtn:SetPoint("BOTTOMRIGHT", frame, "BOTTOMRIGHT", -PAD, 32)
  -- Second row: look around the route without changing it, point the arrow anywhere, find a vendor.
  x, row = PAD, 8
  frame.prevBtn = btn("< Prev", "Look at the step before. Nothing is marked done or undone.", function() DruidKit_StepView(-1) end)
  frame.nextBtn = btn("Next >", "Look at the next step. Nothing is marked done or undone.", function() DruidKit_StepView(1) end)
  frame.goBtn = btn("Go", "Point the arrow at the step you're looking at (do things in your own order). "
    .. "The route arrow comes back when you arrive, or with Now.", function() DruidKit_StepGo() end)
  frame.nowBtn = btn("Now", "Back to your current step and its arrow.", function() DruidKit_StepView(0) end)
  frame.vendorBtn = btn("Vendor", "Point the arrow at the nearest vendor in this zone.", function() DruidKit_StepsCommand("vendor") end)
end

local function textH(f)
  local t = f:GetText()
  if not t or t == "" then return 0 end
  return f:GetStringHeight() or 0
end

local function resize()
  local h = 8 + 14 + 6 + textH(frame.main) + 4 + textH(frame.detail) + 6 + textH(frame.next) + 8 + 20 + 4 + 20 + 8
  frame:SetHeight(math.max(96, h))
end

local function draw()
  if not frame then return end
  local cur = view or pos
  local st = steps[cur]
  if not st then
    frame.head:SetText("Druid Kit route"); frame.stats:SetText("")
    frame.main:SetText(Y .. "Route finished." .. R .. " Say \"update\" for the next part.")
    frame.detail:SetText(""); frame.next:SetText("")
    resize()
    return
  end
  if view and view ~= pos then
    frame.head:SetText(("Viewing %d/%d (you're on %d)  ·  %s"):format(view, #steps, pos, st.sec or ""))
  else
    frame.head:SetText(("Step %d/%d  ·  %s"):format(pos, #steps, st.sec or ""))
  end
  local c = DB.cur
  local stats = ""
  if not view and c and c.i == pos and c.secs >= 30 then
    stats = clock(c.secs) .. (st.est and (" / ~" .. st.est .. "m") or "")
  end
  if c and c.i == pos and c.deaths > 0 then
    stats = stats .. (stats ~= "" and "  " or "") .. c.deaths .. (c.deaths == 1 and " death" or " deaths")
  end
  frame.stats:SetText(stats)
  frame.main:SetText(mainLine(st))
  local adv = adviceLine(st)
  local det = detailLines(st)
  frame.detail:SetText(adv and ((det ~= "" and (det .. "\n") or "") .. adv) or det)
  local nxt = {}
  for i = cur + 1, math.min(#steps, cur + 2) do table.insert(nxt, "Then: " .. shortLine(steps[i])) end
  frame.next:SetText(table.concat(nxt, "\n"))
  resize()
end

-- Advancing ------------------------------------------------------------------------------------
local function evaluate()
  if not DB then return end
  local moved = false
  while pos <= #steps and isDone(pos) do
    local k = steps[pos].q or steps[pos].name
    if not DB.manual[pos] and not (k and DB.skipQ[k]) then logStep(pos, "done") end
    pos = pos + 1; moved = true
  end
  DB.routeStep = pos
  if view and view <= pos then view = nil end
  if moved then customNav = false end
  if moved or not DB.cur or DB.cur.i ~= pos then lastArrowFor = nil; startStats() end
  pointArrow()
  draw()
end
DruidKit_StepsEvaluate = function() pcall(evaluate) end

-- Prev / Next / Now: look through the route without changing it. d = -1, 1, or 0 (back to the current step).
function DruidKit_StepView(d)
  if d == 0 then
    view = nil; customNav = false; lastArrowFor = nil
    pointArrow(); draw()
    return
  end
  local v = math.max(1, math.min(#steps, (view or pos) + d))
  view = (v ~= pos) and v or nil
  draw()
end

-- Go: point the arrow at the step you're looking at (its waypoints first, like the route would).
function DruidKit_StepGo()
  local st = steps[view or pos]
  if not st then return end
  local target = st.at or (st.via and st.via[1])
  if not target or not DruidKit_GoTo then
    say("this step has no map spot. Try the step after it.")
    return
  end
  local label = st.npc or st.text or st.name or st.to or "step"
  DruidKit_GoTo(target[1], target[2], target[3], (not st.at and (target[4] or "way") .. "  >  " or "") .. label, true)
  customNav = (view ~= nil and view ~= pos)
  if not customNav then lastArrowFor = nil; pointArrow() end
  say("arrow set to " .. label .. (customNav and ". The route arrow comes back when you arrive there, or with Now." or "."))
end

-- For the bag check: how many steps until the route deals with a quest, and the next bank on the route.
local BANK_ZONES = { ["Stormwind City"] = true, ["Ironforge"] = true, ["Darnassus"] = true }
DruidKit_StepsAhead = function(q)
  if not q then return nil end
  for i = pos, #steps do
    if steps[i].q == q then return i - pos end
  end
end
DruidKit_NextBank = function(within)
  for i = pos, math.min(#steps, pos + (within or 30)) do
    local at = steps[i].at
    if at and BANK_ZONES[at[1]] then return { steps = i - pos, where = at[1] } end
  end
end

-- Catch-up: when the route is (re)loaded behind where you really are, jump to just after the last quest you've
-- handed in. Steps passed on the way are logged "passed"; their quests stay behind unless they're in your log,
-- and the next update re-plans them.
local function catchUp()
  local last = 0
  for i = #steps, 1, -1 do
    local st = steps[i]
    if st["do"] == "turnin" and st.q and turnedIn(st.q) then last = i; break end
  end
  if last < pos then return 0 end
  -- Stop at the first quest still in your log: you're working there, and a quest handed in early (out of order)
  -- must not pass the steps between (seen 18 Nov: Everstill Bridge handed in early passed Shadow Magic + Tharil'zun).
  local n = 0
  for i = pos, last do
    local st = steps[i]
    if not isDone(i) then
      if st.q and (st["do"] == "accept" or st["do"] == "complete" or st["do"] == "turnin") then
        if logEntry(st.q, st.name) then break end
        DB.passedQ[st.q] = true; n = n + 1; logStep(i, "passed")
      else
        DB.manual[i] = true; n = n + 1; logStep(i, "passed")
      end
    end
  end
  return n
end
DruidKit_StepsCatchUp = function()
  local before = pos
  local ok, n = pcall(catchUp)
  pcall(evaluate)
  if ok and n and n > 0 then
    say(("caught up with you: %d step%s behind you passed (from step %d to %d). The Back button goes back one step.")
      :format(n, n == 1 and "" or "s", before, pos))
  end
end

function DruidKit_StepDone()
  if not steps[pos] then return end
  logStep(pos, "ticked")
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
  viaAt[pos] = nil
  DB.routeStep = pos
  lastArrowFor = nil
  pointArrow(); draw()
end

-- Skip: leave this quest (every step of it) for now. Recorded for the next re-plan.
function DruidKit_StepSkip()
  local st = steps[pos]
  if not st then return end
  local key = st.q or st.name
  logStep(pos, "skipped")
  if key and (st["do"] == "complete" or st["do"] == "turnin" or st["do"] == "accept") then
    DB.skipQ[key] = { name = st.name, lvl = (xpNow()), deaths = DB.cur and DB.cur.deaths or 0,
      secs = DB.cur and math.floor(DB.cur.secs) or 0, at = date and date("%Y-%m-%d %H:%M") }
    say(("skipped %s for now. Your quest log keeps it; the next update decides drop or come back. /dk steps unskip undoes this."):format(st.name or "this quest"))
  else
    DB.manual[pos] = true
  end
  pos = pos + 1
  lastArrowFor = nil
  evaluate()
end

local popBtn
local function showPop(show)
  if not popBtn then
    popBtn = CreateFrame("Button", "DruidKitStepsShow", UIParent, "UIPanelButtonTemplate")
    popBtn:SetSize(64, 20); popBtn:SetText("Route")
    popBtn:SetPoint("TOPRIGHT", frame, "TOPRIGHT", 0, 0)
    popBtn:SetScript("OnClick", function() DruidKit_ToggleSteps(true) end)
    popBtn:SetScript("OnEnter", function(s) GameTooltip:SetOwner(s, "ANCHOR_LEFT"); GameTooltip:SetText("Show the route steps and arrow (Alt+N).", 1, 1, 1, 1, true); GameTooltip:Show() end)
    popBtn:SetScript("OnLeave", function() GameTooltip:Hide() end)
  end
  if show then popBtn:Show() else popBtn:Hide() end
end

-- Show or hide the step window together with its arrow (Alt+N, /dk steps, the Hide/Route buttons).
function DruidKit_ToggleSteps(show)
  if not DB then return end
  if not frame then build() end
  if show == nil then show = not frame:IsShown() end
  DB.stepsHidden = not show
  if show then
    frame:Show(); showPop(false); lastArrowFor = nil; evaluate()
  else
    frame:Hide(); showPop(#steps > 0)
    if DruidKit_NavClear and DruidKit_NavTarget and DruidKit_NavTarget() then DruidKit_NavClear(true) end
  end
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
  "QUEST_DETAIL", "QUEST_PROGRESS", "QUEST_COMPLETE", "GOSSIP_SHOW", "QUEST_GREETING", "PLAYER_DEAD",
  "TAXIMAP_OPENED", "CHAT_MSG_SYSTEM", "HEARTHSTONE_BOUND", "BAG_UPDATE_DELAYED" }) do
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
    DB.skipQ = DB.skipQ or {}
    DB.stepLog = DB.stepLog or {}
    titleDone = DB.titleDone
    flatten()
    local id = DruidKitRoute and DruidKitRoute.id
    DB.passedQ = DB.passedQ or {}
    if DB.routeId ~= id then
      DB.routeId = id; DB.routeStep = 1; DB.manual = {}; DB.skipQ = {}; DB.passedQ = {}; DB.cur = nil
    end
    pos = DB.routeStep or 1
    DruidKit_ToggleSteps(not DB.stepsHidden and #steps > 0)
    -- The quest log isn't ready at login; catch up a few seconds later.
    C_Timer.After(4, function() DruidKit_StepsCatchUp() end)
    return
  end
  if not DB then return end
  if e == "PLAYER_DEAD" then
    if DB.cur and DB.cur.i == pos then
      DB.cur.deaths = DB.cur.deaths + 1
      local st = steps[pos]
      if st and DB.cur.deaths == 2 then
        say(("2 deaths on %s. %s"):format(st.name or "this step", st.party and "Try a group (/4 LFG), or press Skip on the step window."
          or "Press Skip on the step window to leave it for now; the next update re-plans it."))
      end
    end
    pcall(draw)
  elseif e == "QUEST_TURNED_IN" then
    local t = a1 and C_QuestLog and C_QuestLog.GetTitleForQuestID and safe(C_QuestLog.GetTitleForQuestID, a1)
    if t then titleDone[t] = true end
    soon()
  elseif e == "BAG_UPDATE_DELAYED" then
    local now = (GetTime and GetTime()) or 0
    local bl = bagLine()
    if bl and now - lastBagSay > 300 then lastBagSay = now; say(bl) end
    pcall(draw)
  elseif e == "TAXIMAP_OPENED" then
    -- Talking to a flight master learns its flight path, so an "fp" step here is done.
    local st = steps[pos]
    if st and st["do"] == "fp" then DB.manual[pos] = true end
    C_Timer.After(0.5, soon)
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

DruidKit_OnNavStuck = function(label)
  local st = steps[pos]
  if st and DB.cur and DB.cur.i == pos then DB.cur.stuck = (DB.cur.stuck or 0) + 1 end
  say(("not getting closer to %s. The way may be blocked: go round, or open the map (M). If you find the way in, "
    .. "the route learns it from your path."):format(label or "the target"))
end

-- Arrival at the current step's spot (from the navigation arrow).
DruidKit_OnArrive = function()
  if customNav then   -- reached the vendor: back to the route
    customNav = false; lastArrowFor = nil; pointArrow()
    return
  end
  local st = steps[pos]
  local v = st and nextVia(st)
  if v then
    viaAt[pos] = (viaAt[pos] or 0) + 1
    lastArrowFor = nil
    pointArrow(); pcall(draw)
    return
  end
  if st and st.at and (st["do"] == "goto" or st["do"] == "fly" or st["do"] == "hearth") then
    arrived[pos] = true
    soon()
  end
end

-- Keep progress text fresh while you work on a "Do" step.
local tick = 0
ev:SetScript("OnUpdate", function(_, el)
  if DB and DB.cur and DB.cur.i == pos and not (UnitIsAFK and UnitIsAFK("player")) then DB.cur.secs = DB.cur.secs + el end
  tick = tick + el
  if tick < 2 then return end
  tick = 0
  pcall(recordTrail)
  if frame and frame:IsShown() and steps[pos] then pcall(draw) end
end)

-- /dk steps | /dk steps reset | /dk auto
function DruidKit_StepsCommand(arg)
  arg = (arg or ""):lower()
  if arg == "reset" then
    DB.manual = {}; DB.passedQ = {}; pos = 1; DB.routeStep = 1; arrived = {}; lastArrowFor = nil
    DruidKit_ToggleSteps(true)
    say("route restarted: finished steps skip themselves.")
  elseif arg == "unskip" then
    local n = 0
    for k in pairs(DB.skipQ) do DB.skipQ[k] = nil; n = n + 1 end
    pos = 1; lastArrowFor = nil; evaluate()
    say(("%d skipped quest%s back in the route."):format(n, n == 1 and " is" or "s are"))
  elseif arg == "log" then
    say("last steps (actual vs projected):")
    for i = math.max(1, #DB.stepLog - 9), #DB.stepLog do
      local l = DB.stepLog[i]
      print(("  %s %s: %s%s, %d death%s, %d XP"):format(l.how, l.name or l["do"], clock(l.secs),
        l.est and (" / ~" .. l.est .. "m") or "", l.deaths, l.deaths == 1 and "" or "s", l.xp or 0))
    end
  elseif arg == "auto" then
    DB.autoQuests = DB.autoQuests == false
    say("automatic quest accept and hand-in " .. (DB.autoQuests == false and "OFF." or "ON (hold Shift to do it yourself)."))
  elseif arg == "vendor" then
    local v = nearestVendor()
    if v and DruidKit_GoTo then
      DruidKit_GoTo(v[1], v[2], v[3], "Vendor: " .. v[4], true)
      lastArrowFor = pos   -- keep the vendor arrow until you arrive or the step changes
      customNav = true
      say("arrow set to " .. v[4] .. (v[5] ~= "" and (" (" .. v[5] .. ")") or "") .. ". Sell, then carry on.")
    else
      say("no vendor known in this zone. Sell at the next town.")
    end
  elseif arg == "keymap" or arg == "keys" then
    if DruidKit_ShowKeymap then DruidKit_ShowKeymap() end
  elseif arg == "vendorprompt" then
    DB.vendorPrompt = DB.vendorPrompt == false
    say("bags-full vendor message " .. (DB.vendorPrompt == false and "OFF (the Vendor button still works)." or "ON."))
    pcall(draw)
  elseif arg == "arrow" then
    DB.arrowOff = not DB.arrowOff
    say("route arrow " .. (DB.arrowOff and "OFF." or "ON."))
    lastArrowFor = nil; pointArrow()
  else
    DruidKit_ToggleSteps()
  end
end
