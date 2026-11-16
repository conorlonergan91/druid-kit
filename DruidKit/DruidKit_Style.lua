-- Druid Kit: shared look for list windows (Bag check, Bank check).
-- Same frame as the guide: portrait frame, Restoration-tree backdrop, green tint, Druid orange accents.

local S = {}
DruidKitStyle = S

S.ORANGE = { 1, 0.49, 0.04 }
S.LEAF = { 0.5, 0.83, 0.36 }

local function newFrame(kind, name, parent, template)
  local ok, f = pcall(CreateFrame, kind, name, parent, template)
  if ok and f then return f end
  return CreateFrame(kind, name, parent, "BasicFrameTemplateWithInset")
end

-- A movable window with a scrolling list area. Returns the frame; f.list is where rows go.
function S.window(name, title, icon, w, h)
  local f = newFrame("Frame", name, UIParent, "PortraitFrameTemplate")
  f:SetSize(w or 400, h or 470)
  f:SetFrameStrata("DIALOG")
  f:SetMovable(true); f:EnableMouse(true); f:SetClampedToScreen(true)
  f:RegisterForDrag("LeftButton")
  f:SetScript("OnDragStart", f.StartMoving)
  f:SetScript("OnDragStop", f.StopMovingOrSizing)
  table.insert(UISpecialFrames, name)
  if f.SetPortraitToAsset then pcall(f.SetPortraitToAsset, f, icon)
  elseif f.portrait and SetPortraitToTexture then pcall(SetPortraitToTexture, f.portrait, icon) end
  if f.SetTitle then pcall(f.SetTitle, f, title)
  else
    local t = f:CreateFontString(nil, "OVERLAY", "GameFontHighlight")
    t:SetPoint("TOP", 0, -6); t:SetText(title)
  end

  f.sub = f:CreateFontString(nil, "OVERLAY", "GameFontNormalSmall")
  f.sub:SetPoint("TOPLEFT", f, "TOPLEFT", 64, -38)
  f.sub:SetPoint("RIGHT", f, "RIGHT", -16, 0)
  f.sub:SetJustifyH("LEFT")

  local inset = CreateFrame("Frame", nil, f, "InsetFrameTemplate")
  inset:SetPoint("TOPLEFT", f, "TOPLEFT", 10, -62)
  inset:SetPoint("BOTTOMRIGHT", f, "BOTTOMRIGHT", -8, 34)
  local bg = inset:CreateTexture(nil, "BACKGROUND", nil, 1)
  bg:SetPoint("TOPLEFT", 3, -3); bg:SetPoint("BOTTOMRIGHT", -3, 3)
  if bg:SetTexture("Interface\\TalentFrame\\DruidRestoration-TopLeft") == false then bg:Hide() end
  bg:SetAlpha(0.3)
  local tint = inset:CreateTexture(nil, "BACKGROUND", nil, 2)
  tint:SetAllPoints(bg)
  tint:SetColorTexture(0.03, 0.10, 0.04, 0.6)

  local scroll = CreateFrame("ScrollFrame", nil, inset, "UIPanelScrollFrameTemplate")
  scroll:SetPoint("TOPLEFT", inset, "TOPLEFT", 8, -8)
  scroll:SetPoint("BOTTOMRIGHT", inset, "BOTTOMRIGHT", -28, 8)
  local list = CreateFrame("Frame", nil, scroll)
  list:SetSize((w or 400) - 60, 10)
  scroll:SetScrollChild(list)
  f.list, f.scroll = list, scroll

  f.footer = f:CreateFontString(nil, "OVERLAY", "GameFontDisableSmall")
  f.footer:SetPoint("BOTTOMLEFT", f, "BOTTOMLEFT", 16, 12)
  f.footer:SetPoint("RIGHT", f, "RIGHT", -120, 0)
  f.footer:SetJustifyH("LEFT")

  f.pool = { header = {}, item = {}, note = {} }
  f:Hide()
  return f
end

-- Layout helper: call begin(), then header/item/note in order, then finish().
function S.begin(f)
  f.y = -4
  f.used = { header = 0, item = 0, note = 0 }
  f.stripe = false
end

local function take(f, kind, make)
  f.used[kind] = f.used[kind] + 1
  local p = f.pool[kind][f.used[kind]]
  if not p then p = make(); f.pool[kind][f.used[kind]] = p end
  p:ClearAllPoints()
  p:SetPoint("TOPLEFT", f.list, "TOPLEFT", 0, f.y)
  p:SetPoint("RIGHT", f.list, "RIGHT", 0, 0)
  p:Show()
  return p
end

-- Section title with an icon, a count on the right and an orange rule underneath.
function S.header(f, text, icon, count, btnText, onClick)
  if f.used.header > 0 or f.used.item > 0 then f.y = f.y - 10 end
  local h = take(f, "header", function()
    local h = CreateFrame("Frame", nil, f.list)
    h:SetHeight(26)
    h.icon = h:CreateTexture(nil, "ARTWORK"); h.icon:SetSize(18, 18); h.icon:SetPoint("LEFT", 2, 2)
    h.icon:SetTexCoord(0.08, 0.92, 0.08, 0.92)
    h.text = h:CreateFontString(nil, "OVERLAY", "GameFontNormal")
    h.text:SetPoint("LEFT", h.icon, "RIGHT", 8, 0)
    h.count = h:CreateFontString(nil, "OVERLAY", "GameFontDisableSmall")
    h.count:SetPoint("LEFT", h.text, "RIGHT", 6, 0)
    h.rule = h:CreateTexture(nil, "ARTWORK")
    h.rule:SetHeight(1)
    h.rule:SetPoint("BOTTOMLEFT", 0, 0); h.rule:SetPoint("BOTTOMRIGHT", 0, 0)
    h.rule:SetColorTexture(S.ORANGE[1], S.ORANGE[2], S.ORANGE[3], 0.45)
    h.btn = CreateFrame("Button", nil, h, "UIPanelButtonTemplate")
    h.btn:SetSize(72, 20); h.btn:SetPoint("RIGHT", -2, 2)
    return h
  end)
  h.icon:SetTexture(icon)
  h.text:SetText(text)
  h.count:SetText(count and count > 0 and ("(" .. count .. ")") or "")
  if btnText then h.btn:SetText(btnText); h.btn:SetScript("OnClick", onClick); h.btn:Show() else h.btn:Hide() end
  f.y = f.y - 30
  f.stripe = false
  return h
end

-- An item card: icon with quality border, coloured name, a grey reason line, optional button.
function S.item(f, link, icon, quality, title, detail, btnText, onClick)
  local r = take(f, "item", function()
    local r = CreateFrame("Button", nil, f.list)
    r:SetHeight(38)
    r.bg = r:CreateTexture(nil, "BACKGROUND"); r.bg:SetAllPoints()
    r.hl = r:CreateTexture(nil, "HIGHLIGHT"); r.hl:SetAllPoints(); r.hl:SetColorTexture(S.LEAF[1], S.LEAF[2], S.LEAF[3], 0.12)
    r.border = r:CreateTexture(nil, "ARTWORK", nil, 1); r.border:SetSize(30, 30); r.border:SetPoint("LEFT", 6, 0)
    r.icon = r:CreateTexture(nil, "ARTWORK", nil, 2); r.icon:SetSize(28, 28); r.icon:SetPoint("CENTER", r.border)
    r.icon:SetTexCoord(0.08, 0.92, 0.08, 0.92)
    r.name = r:CreateFontString(nil, "OVERLAY", "GameFontHighlight")
    r.name:SetPoint("TOPLEFT", r.border, "TOPRIGHT", 10, -1)
    r.name:SetPoint("RIGHT", r, "RIGHT", -84, 0); r.name:SetJustifyH("LEFT"); r.name:SetWordWrap(false)
    r.detail = r:CreateFontString(nil, "OVERLAY", "GameFontDisableSmall")
    r.detail:SetPoint("BOTTOMLEFT", r.border, "BOTTOMRIGHT", 10, 1)
    r.detail:SetPoint("RIGHT", r, "RIGHT", -84, 0); r.detail:SetJustifyH("LEFT"); r.detail:SetWordWrap(false)
    r.btn = CreateFrame("Button", nil, r, "UIPanelButtonTemplate")
    r.btn:SetSize(70, 22); r.btn:SetPoint("RIGHT", -6, 0)
    r:SetScript("OnEnter", function(s)
      if s.link then GameTooltip:SetOwner(s, "ANCHOR_LEFT"); GameTooltip:SetHyperlink(s.link); GameTooltip:Show() end
    end)
    r:SetScript("OnLeave", function() GameTooltip:Hide() end)
    return r
  end)
  f.stripe = not f.stripe
  r.bg:SetColorTexture(1, 1, 1, f.stripe and 0.04 or 0)
  r.link = link
  r.icon:SetTexture(icon or "Interface\\Icons\\INV_Misc_QuestionMark")
  local c = (ITEM_QUALITY_COLORS and ITEM_QUALITY_COLORS[quality or 1]) or { r = 1, g = 1, b = 1 }
  r.border:SetColorTexture(c.r, c.g, c.b, 0.9)
  r.name:SetText(title)
  r.name:SetTextColor(c.r, c.g, c.b)
  r.detail:SetText(detail or "")
  if btnText then r.btn:SetText(btnText); r.btn:SetScript("OnClick", onClick); r.btn:Show() else r.btn:Hide() end
  f.y = f.y - 40
  return r
end

-- A quiet line of text (empty states, tips).
function S.note(f, text)
  local n = take(f, "note", function()
    local n = CreateFrame("Frame", nil, f.list)
    n:SetHeight(20)
    n.text = n:CreateFontString(nil, "OVERLAY", "GameFontDisable")
    n.text:SetPoint("TOPLEFT", 8, -2); n.text:SetPoint("RIGHT", -6, 0)
    n.text:SetJustifyH("LEFT"); n.text:SetWordWrap(true)
    return n
  end)
  n.text:SetText(text)
  local h = math.max(18, (n.text:GetStringHeight() or 14) + 6)
  n:SetHeight(h)
  f.y = f.y - h
  return n
end

function S.finish(f)
  for kind, list in pairs(f.pool) do
    for i = f.used[kind] + 1, #list do list[i]:Hide() end
  end
  f.list:SetHeight(-f.y + 8)
end
